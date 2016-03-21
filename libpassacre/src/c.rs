/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, path, ptr, slice, str, sync, io};
use std::cell::RefCell;
use std::panic::{AssertRecoverSafe, RecoverSafe, recover};

use ::error::PassacreErrorKind::*;
use ::error::{PassacreError, PassacreResult};
use ::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
use ::multibase::{Base, MultiBase};
use ::util::clone_from_slice;


macro_rules! recompose {
    ($name:ident, $length:expr) => {
        let $name = {
            let length = $length as usize;
            if $name.is_null() && length != 0 {
                fail!(UserError);
            }
            unsafe { slice::from_raw_parts($name, length) }
        };
    };
    (mut $name:ident, $length:expr) => {
        let mut $name = {
            let length = $length as usize;
            if $name.is_null() && length != 0 {
                fail!(UserError);
            }
            AssertRecoverSafe::new(unsafe { slice::from_raw_parts_mut($name, length) })
        };
    };
}


pub type AllocatorFn = extern fn(::libc::size_t, *const ::libc::c_void) -> *mut ::libc::c_uchar;

struct Allocator {
    allocator: AllocatorFn,
    context: *const ::libc::c_void,
}

impl Allocator {
    fn new(allocator: AllocatorFn, context: *const ::libc::c_void) -> Allocator {
        Allocator { allocator: allocator, context: context }
    }

    fn string_copy(&self, s: String) -> PassacreResult<()> {
        let output = (self.allocator)(s.len() as ::libc::size_t, self.context);
        if output.is_null() {
            fail!(AllocatorError);
        }
        recompose!(mut output, s.len());
        clone_from_slice(&mut *output, s.as_bytes());
        Ok(())
    }
}


thread_local!(static ERROR_STRING: RefCell<String> = RefCell::new(String::new()));


struct ErrorStringWriter;

impl io::Write for ErrorStringWriter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        let buf = match str::from_utf8(buf) {
            Ok(buf) => buf,
            _ => return Err(io::Error::new(io::ErrorKind::InvalidInput, "invalid utf-8")),
        };
        ERROR_STRING.with(|error_string| {
            let mut error_string = error_string.borrow_mut();
            error_string.push_str(buf);
        });
        Ok(buf.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}


macro_rules! force_block {
    ($b:block) => ($b);
}

unsafe fn drop_ptr<T>(p: *const T) {
    // read the pointer and do nothing with the result, so that the value
    // immediately goes out of scope and is dropped. you can't move a value out
    // of dereferencing a *mut, and passing a &mut to mem::drop is a no-op.
    ptr::read(p);
}


macro_rules! c_export {
    ($name:ident, ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        #[no_mangle]
        #[allow(unused_mut)]
        pub extern "C" fn $name( $($arg : $argtype,)* ) -> ::libc::c_int {
            let closure = move || force_block!({
                $($preamble)*
                let closure = move || {
                    ERROR_STRING.with(|error_string| error_string.borrow_mut().clear());
                    let panic_sink = Box::new(ErrorStringWriter);
                    let prev_sink = io::set_panic(panic_sink);
                    let mut inner = move || $body;
                    let result = inner();
                    io::set_panic(prev_sink.unwrap_or_else(|| Box::new(io::sink())));
                    result
                };
                match recover(closure) {
                    Ok(r) => r,
                    Err(_) => Err(Panic.to_error()),
                }
            });
            match closure() {
                Ok(()) => 0,
                Err(e) => e.to_c_int(),
            }
        }
    };
}


fn null_check<'a, T>(p: *const T, null_allowed: bool) -> PassacreResult<Option<&'a T>> {
    if p.is_null() {
        if null_allowed {
            Ok(None)
        } else {
            fail!(UserError)
        }
    } else {
        Ok(Some(unsafe { &*p }))
    }
}

fn null_check_mut<'a, T>(p: *mut T, null_allowed: bool) -> PassacreResult<Option<&'a mut T>> {
    if p.is_null() {
        if null_allowed {
            Ok(None)
        } else {
            fail!(UserError)
        }
    } else {
        Ok(Some(unsafe { &mut *p }))
    }
}

macro_rules! resolve_ptr {
    ($func:ident, $ptr:expr, $null_allowed:expr) => {
        match try!($func($ptr, $null_allowed)) {
            Some(r) => r,
            None => return Ok(()),
        }
    };
}


pub type CMultiBase = sync::Mutex<MultiBase>;

macro_rules! passacre_mb_export {
    ($name:ident, $mb:ident, $null_allowed:expr,
     ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        c_export!($name, ( mb: *const CMultiBase $(,$arg : $argtype)* ), {
            let mb_mutex = resolve_ptr!(null_check, mb, $null_allowed);
            $($preamble)*
        }, {
            let mut $mb = try!(mb_mutex.lock());
            $body
        });
    };
}


#[no_mangle]
pub extern "C" fn passacre_mb_size() -> ::libc::size_t {
    mem::size_of::<CMultiBase>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_mb_align() -> ::libc::size_t {
    mem::align_of::<CMultiBase>() as ::libc::size_t
}

c_export!(passacre_mb_init, (mb: *mut CMultiBase), {}, {
    let p = sync::Mutex::new(MultiBase::new());
    unsafe { ptr::write(mb, p); }
    Ok(())
});

passacre_mb_export!(passacre_mb_required_bytes, mb, false, (dest: *mut ::libc::size_t), {
    let mut dest = AssertRecoverSafe::new(resolve_ptr!(null_check_mut, dest, false));
}, {
    let ret = mb.required_bytes();
    **dest = ret as ::libc::size_t;
    Ok(())
});

passacre_mb_export!(passacre_mb_entropy_bits, mb, false, (dest: *mut ::libc::size_t), {
    let mut dest = AssertRecoverSafe::new(resolve_ptr!(null_check_mut, dest, false));
}, {
    let ret = mb.entropy_bits();
    **dest = ret as ::libc::size_t;
    Ok(())
});

passacre_mb_export!(passacre_mb_enable_shuffle, mb, false, (), {}, {
    mb.enable_shuffle();
    Ok(())
});

passacre_mb_export!(passacre_mb_add_base, mb, false, (
    which: ::libc::c_uint, string: *const u8, string_length: ::libc::size_t), {
    recompose!(string, string_length);
}, {
    let base = try!(Base::of_c_parts(which, string));
    mb.add_base(base)
});

c_export!(passacre_mb_add_sub_mb, (parent: *const CMultiBase, child: *const CMultiBase), {
    if parent == child {
        fail!(UserError);
    }
    let parent = resolve_ptr!(null_check, parent, false);
    let child = resolve_ptr!(null_check, child, false);
}, {
    let mut parent = try!(parent.lock());
    let child = try!(child.lock());
    parent.add_base(Base::NestedBase(child.clone()))
});

passacre_mb_export!(passacre_mb_load_words_from_path, mb, false,
                    (path: *const u8, path_length: ::libc::size_t), {
    recompose!(path, path_length);
}, {
    // XXX: better error handling
    let path = path::Path::new(str::from_utf8(path).unwrap());
    mb.load_words_from_path(path)
});

passacre_mb_export!(passacre_mb_encode_from_bytes, mb, false,
                    (input: *const u8, input_length: ::libc::size_t,
                     allocator_fn: AllocatorFn, context: *const ::libc::c_void), {
    recompose!(input, input_length);
    let allocator = Allocator::new(allocator_fn, context);
}, {
    let ret = try!(mb.encode_from_bytes(input));
    try!(allocator.string_copy(ret));
    Ok(())
});

c_export!(passacre_mb_finished, (mb: *const CMultiBase), {}, {
    unsafe { drop_ptr(mb); }
    Ok(())
});


pub type CPassacreGenerator<'a> = sync::Mutex<PassacreGenerator<'a>>;

macro_rules! passacre_gen_export {
    ($name:ident, $gen:ident, $null_allowed:expr,
     ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        c_export!($name, ( gen: *const CPassacreGenerator $(,$arg : $argtype)* ), {
            let gen_mutex = resolve_ptr!(null_check, gen, $null_allowed);
            $($preamble)*
        }, {
            let mut $gen = try!(gen_mutex.lock());
            $body
        });
    };
}


#[no_mangle]
pub extern "C" fn passacre_gen_size() -> ::libc::size_t {
    mem::size_of::<CPassacreGenerator>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_gen_align() -> ::libc::size_t {
    mem::align_of::<CPassacreGenerator>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_gen_scrypt_buffer_size() -> ::libc::size_t {
    SCRYPT_BUFFER_SIZE as ::libc::size_t
}


c_export!(passacre_gen_init, (gen: *mut CPassacreGenerator, algorithm: ::libc::c_uint), {}, {
    testing_panic!(algorithm == 99);
    let algorithm = try!(Algorithm::of_c_uint(algorithm));
    let p = try!(PassacreGenerator::new(algorithm));
    let p = sync::Mutex::new(p);
    unsafe { ptr::write(gen, p); }
    Ok(())
});

passacre_gen_export!(passacre_gen_use_scrypt, gen, false,
                     (n: u64, r: u32, p: u32, persistence_buffer: *mut u8), {
    let buf = try!(null_check_mut(persistence_buffer as *mut [u8; SCRYPT_BUFFER_SIZE], true));
    let kdf = Kdf::new_scrypt(n, r, p, buf);
}, {
    gen.use_kdf(kdf)
});


passacre_gen_export!(passacre_gen_absorb_username_password_site, gen, false,
                     (username: *const ::libc::c_uchar, username_length: ::libc::size_t,
                      password: *const ::libc::c_uchar, password_length: ::libc::size_t,
                      site: *const ::libc::c_uchar, site_length: ::libc::size_t), {
    recompose!(username, username_length);
    recompose!(password, password_length);
    recompose!(site, site_length);
}, {
    gen.absorb_username_password_site(username, password, site)
});


passacre_gen_export!(passacre_gen_absorb_null_rounds, gen, false,
                     (n_rounds: ::libc::size_t), {}, {
    gen.absorb_null_rounds(n_rounds as usize)
});


passacre_gen_export!(passacre_gen_squeeze, gen, false,
                     (output: *mut ::libc::c_uchar, output_length: ::libc::size_t), {
    recompose!(mut output, output_length);
}, {
    gen.squeeze(&mut *output)
});

passacre_gen_export!(passacre_gen_squeeze_password, gen, false,
                     (mb: *const CMultiBase, allocator_fn: AllocatorFn,
                      context: *const ::libc::c_void), {
    let mb = resolve_ptr!(null_check, mb, false);
    let allocator = Allocator::new(allocator_fn, context);
}, {
    let mut mb = try!(mb.lock());
    allocator.string_copy(try!(mb.encode_from_generator(&mut *gen)))
});

c_export!(passacre_gen_finished, (gen: *const CPassacreGenerator), {}, {
    unsafe { drop_ptr(gen); }
    Ok(())
});


struct ByteCopier<'a> {
    dest: &'a mut [u8],
    copied: Option<usize>,
}

impl<'a> ByteCopier<'a> {
    fn new(dest_p: *mut u8, dest_length: usize) -> ByteCopier<'a> {
        let dest = unsafe { slice::from_raw_parts_mut(dest_p, dest_length as usize) };
        ByteCopier { dest: dest, copied: None }
    }

    fn copy(&mut self, bytes: &[u8]) {
        if self.copied.is_some() {
            return
        }
        self.copied = Some(clone_from_slice(self.dest, bytes));
    }

    fn copied_with_default(&mut self, default: &[u8]) -> usize {
        self.copy(default);
        self.copied.unwrap()
    }
}

impl<'a> RecoverSafe for ByteCopier<'a> {}


#[no_mangle]
pub extern "C" fn passacre_error(which: ::libc::c_int, dest_p: *mut ::libc::c_uchar,
                                 dest_length: ::libc::size_t) -> ::libc::size_t {
    let mut copier = ByteCopier::new(dest_p, dest_length as usize);
    let closure_result = {
        let closure = move || {
            testing_panic!(which == -99);
            let err = PassacreError::of_c_int(which);
            let err_str = match err {
                Some(PassacreError { kind: Panic, .. }) => {
                    if ERROR_STRING.with(|err_string| {
                        let err_string = err_string.borrow();
                        if err_string.is_empty() {
                            return false;
                        }
                        copier.copy(err_string.as_bytes());
                        return true;
                    }) {
                        return copier;
                    } else {
                        "unknown panic"
                    }
                },
                Some(e) => e.to_string(),
                None => "unknown error",
            };
            copier.copy(err_str.as_bytes());
            copier
        };
        recover(closure)
    };
    let mut copier = match closure_result {
        Ok(c) => c,
        Err(_) => {
            let mut copier = ByteCopier::new(dest_p, dest_length as usize);
            copier.copy("passacre_error: panic".as_bytes());
            copier
        },
    };
    copier.copied_with_default("passacre_error: internal error".as_bytes()) as ::libc::size_t
}
