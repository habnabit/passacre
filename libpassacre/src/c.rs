/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, path, ptr, slice, str, io};
use std::cell::RefCell;
use std::rt::unwind::try;

use ::passacre::{Algorithm, PassacreError, PassacreGenerator, SCRYPT_BUFFER_SIZE};
use ::multibase::{Base, MultiBase};
use ::util::clone_from_slice;


pub type Allocator = extern fn(::libc::size_t, *const ::libc::c_void) -> *mut ::libc::c_uchar;

fn allocator_string_copy(s: String, allocator: Allocator, context: *const ::libc::c_void)
                         -> Result<(), PassacreError> {
    let output = allocator(s.len() as ::libc::size_t, context);
    if output.is_null() {
        return Err(PassacreError::AllocatorError);
    }
    let output = unsafe { slice::from_raw_parts_mut(output, s.len()) };
    clone_from_slice(output, s.as_bytes());
    Ok(())
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


unsafe fn drop_ptr<T>(p: *const T) {
    // read the pointer and do nothing with the result, so that the value
    // immediately goes out of scope and is dropped. you can't move a value out
    // of dereferencing a *mut, and passing a &mut to mem::drop is a no-op.
    ptr::read(p);
}


macro_rules! c_export {
    ($name:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        #[no_mangle]
        pub extern "C" fn $name( $($arg : $argtype,)* ) -> ::libc::c_int {
            let mut result: Option<Result<(), PassacreError>> = None;
            let closure_result = {
                let closure = || {
                    ERROR_STRING.with(|error_string| error_string.borrow_mut().clear());
                    let panic_sink = Box::new(ErrorStringWriter);
                    let prev_sink = io::set_panic(panic_sink);
                    let inner = move || $body;
                    result = Some(inner());
                    io::set_panic(prev_sink.unwrap_or_else(|| Box::new(io::sink())));
                };
                unsafe { try(closure) }
            };
            let ret = match closure_result {
                Ok(()) => match result {
                    Some(Ok(())) => None,
                    Some(Err(e)) => Some(e),
                    None => Some(PassacreError::InternalError),
                },
                Err(_) => Some(PassacreError::Panic),
            };
            match ret {
                Some(e) => e.to_c_int(),
                None => 0,
            }
        }
    };
}


macro_rules! passacre_mb_export {
    ($name:ident, mut $mb:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        c_export!($name, ( mb: *mut MultiBase $(,$arg : $argtype)* ), {
            if mb.is_null() {
                return Err(PassacreError::UserError);
            }
            let mut $mb = unsafe { &mut *mb };
            $body
        });
    };
    ($name:ident, $mb:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        c_export!($name, ( mb: *const MultiBase $(,$arg : $argtype)* ), {
            if mb.is_null() {
                return Err(PassacreError::UserError);
            }
            let $mb = unsafe { &*mb };
            $body
        });
    };
}


#[no_mangle]
pub extern "C" fn passacre_mb_size() -> ::libc::size_t {
    mem::size_of::<MultiBase>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_mb_align() -> ::libc::size_t {
    mem::align_of::<MultiBase>() as ::libc::size_t
}

c_export!(passacre_mb_init, (mb_p: *mut MultiBase), {
    let mb = MultiBase::new();
    unsafe { ptr::write(mb_p, mb); }
    Ok(())
});

passacre_mb_export!(passacre_mb_required_bytes, mb, (dest: *mut ::libc::size_t), {
    let ret = mb.required_bytes();
    unsafe { *dest = ret as ::libc::size_t; }
    Ok(())
});

passacre_mb_export!(passacre_mb_add_base, mut mb, (
    which: ::libc::c_uint, string: *const u8, string_length: ::libc::size_t), {
    let string = unsafe { slice::from_raw_parts(string, string_length as usize) };
    let base = try!(Base::of_c_parts(which, string));
    mb.add_base(base)
});

passacre_mb_export!(passacre_mb_load_words_from_path, mut mb, (path: *const u8, path_length: ::libc::size_t), {
    let path = unsafe { slice::from_raw_parts(path, path_length as usize) };
    // XXX: better error handling
    let path = path::Path::new(str::from_utf8(path).unwrap());
    mb.load_words_from_path(path)
});

passacre_mb_export!(passacre_mb_encode_from_bytes, mb, (
    input: *const u8, input_length: ::libc::size_t, allocator: Allocator, context: *const ::libc::c_void), {
    let input = unsafe { slice::from_raw_parts(input, input_length as usize) };
    let ret = try!(mb.encode_from_bytes(input));
    try!(allocator_string_copy(ret, allocator, context));
    Ok(())
});

c_export!(passacre_mb_finished, (mb: *const MultiBase), {
    if mb.is_null() {
        return Ok(());
    }
    unsafe { drop_ptr(mb); }
    Ok(())
});


macro_rules! passacre_gen_export {
    ($name:ident, $gen:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        c_export!($name, ( gen: *mut PassacreGenerator $(,$arg : $argtype)* ), {
            if gen.is_null() {
                return Err(PassacreError::UserError);
            }
            let mut $gen = unsafe { &mut *gen };
            $body
        });
    };
}


#[no_mangle]
pub extern "C" fn passacre_gen_size() -> ::libc::size_t {
    mem::size_of::<PassacreGenerator>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_gen_align() -> ::libc::size_t {
    mem::align_of::<PassacreGenerator>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_gen_scrypt_buffer_size() -> ::libc::size_t {
    SCRYPT_BUFFER_SIZE as ::libc::size_t
}

c_export!(passacre_gen_init, (gen: *mut PassacreGenerator, algorithm: ::libc::c_uint), {
    let algorithm = try!(Algorithm::of_c_uint(algorithm));
    let p = try!(PassacreGenerator::new(algorithm));
    unsafe { ptr::write(gen, p); }
    Ok(())
});

fn maybe<T, F>(val: T, pred: F) -> Option<T> where F: FnOnce(&T) -> bool {
    if pred(&val) { Some(val) } else { None }
}

passacre_gen_export!(passacre_gen_use_scrypt, gen, (n: u64, r: u32, p: u32,
                                                    persistence_buffer: *mut u8), {
    gen.use_scrypt(n, r, p, maybe(persistence_buffer, |p| !p.is_null()))
});


passacre_gen_export!(passacre_gen_absorb_username_password_site, gen, (
    username: *const ::libc::c_uchar, username_length: ::libc::size_t,
    password: *const ::libc::c_uchar, password_length: ::libc::size_t,
    site: *const ::libc::c_uchar, site_length: ::libc::size_t), {
    let username = unsafe { slice::from_raw_parts(username, username_length as usize) };
    let password = unsafe { slice::from_raw_parts(password, password_length as usize) };
    let site = unsafe { slice::from_raw_parts(site, site_length as usize) };
    gen.absorb_username_password_site(username, password, site)
});


passacre_gen_export!(passacre_gen_absorb_null_rounds, gen, (n_rounds: ::libc::size_t), {
    gen.absorb_null_rounds(n_rounds as usize)
});


passacre_gen_export!(passacre_gen_squeeze, gen, (output: *mut ::libc::c_uchar, output_length: ::libc::size_t), {
    let output = unsafe { slice::from_raw_parts_mut(output, output_length as usize) };
    gen.squeeze(output)
});

passacre_gen_export!(passacre_gen_squeeze_password, gen, (
    mb: *const MultiBase, allocator: Allocator, context: *const ::libc::c_void), {
    if mb.is_null() {
        return Err(PassacreError::UserError);
    }
    let mb = unsafe { &*mb };
    let mut buf = vec![0u8; mb.required_bytes()];
    loop {
        try!(gen.squeeze(&mut buf));
        match mb.encode_from_bytes(&buf) {
            Ok(s) => {
                try!(allocator_string_copy(s, allocator, context));
                break;
            },
            Err(PassacreError::DomainError) => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(())
});

c_export!(passacre_gen_finished, (gen: *const PassacreGenerator), {
    if gen.is_null() {
        return Ok(());
    }
    unsafe { drop_ptr(gen); }
    Ok(())
});

#[no_mangle]
pub extern "C" fn passacre_error(which: ::libc::c_int, dest: *mut ::libc::c_uchar, dest_length: ::libc::size_t)
                                 -> ::libc::size_t {
    let mut result: Option<usize> = None;
    let dest = unsafe { slice::from_raw_parts_mut(dest, dest_length as usize) };
    let closure_result = {
        let closure = || {
            let err = PassacreError::of_c_int(which);
            let err_str = match err {
                Some(PassacreError::Panic) => {
                    if ERROR_STRING.with(|err_string| {
                        let err_string = err_string.borrow();
                        if err_string.is_empty() {
                            return false;
                        }
                        result = Some(clone_from_slice(dest, err_string.as_bytes()));
                        return true;
                    }) {
                        return;
                    } else {
                        "unknown panic"
                    }
                },
                Some(e) => e.to_string(),
                None => "unknown error",
            };
            result = Some(clone_from_slice(dest, err_str.as_bytes()));
        };
        unsafe { try(closure) }
    };
    let ret = match closure_result {
        Ok(()) => match result {
            Some(s) => s,
            None => clone_from_slice(dest, "passacre_error: internal error".as_bytes()),
        },
        Err(_) => clone_from_slice(dest, "passacre_error: panic".as_bytes()),
    };
    ret as ::libc::size_t
}
