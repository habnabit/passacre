/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, path, ptr, slice, str, sync};
use std::cell::RefCell;
use std::panic::{self, AssertUnwindSafe, UnwindSafe, catch_unwind};

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
            AssertUnwindSafe(unsafe { slice::from_raw_parts_mut($name, length) })
        };
    };
}


struct ReifiedPanicInfo {
    file: Option<String>,
    line: Option<u32>,
    payload: String,
}

impl ReifiedPanicInfo {
    fn from_info(info: &panic::PanicInfo) -> ReifiedPanicInfo {
        let payload = if let Some(s) = info.payload().downcast_ref::<String>() {
            s.clone()
        } else if let Some(&s) = info.payload().downcast_ref::<&'static str>() {
            s.into()
        } else {
            "unknown panic payload".into()
        };
        let mut ret = ReifiedPanicInfo {
            file: None,
            line: None,
            payload: payload,
        };
        if let Some(loc) = info.location() {
            ret.file = Some(loc.file().into());
            ret.line = Some(loc.line());
        }
        ret
    }
}

thread_local!(static LAST_PANIC: RefCell<Option<ReifiedPanicInfo>> = RefCell::new(None));

fn install_panic_hook() {
    panic::set_hook(Box::new(|info| {
        LAST_PANIC.with(|opt_ref| {
            *opt_ref.borrow_mut() = Some(ReifiedPanicInfo::from_info(info));
        });
    }));
}

pub type AllocatorFn = extern fn(::libc::size_t, *const ::libc::c_void) -> *mut ::libc::c_uchar;

struct Context {
    allocator: AllocatorFn,
    last_panic: Option<ReifiedPanicInfo>,
}

impl Context {
    fn new(allocator: AllocatorFn) -> Context {
        Context {
            allocator: allocator,
            last_panic: None,
        }
    }

    fn string_copy(&self, closure: *const ::libc::c_void, s: String) -> PassacreResult<()> {
        let output = (self.allocator)(s.len() as ::libc::size_t, closure);
        if output.is_null() {
            fail!(AllocatorError);
        }
        recompose!(mut output, s.len());
        clone_from_slice(&mut *output, s.as_bytes());
        Ok(())
    }
}


unsafe fn drop_ptr<T>(p: *const T) {
    // read the pointer and do nothing with the result, so that the value
    // immediately goes out of scope and is dropped. you can't move a value out
    // of dereferencing a *mut, and passing a &mut to mem::drop is a no-op.
    ptr::read(p);
}


#[repr(C)]
pub struct CPassacreContext(sync::Mutex<Context>);

#[no_mangle]
pub extern "C" fn passacre_ctx_size() -> ::libc::size_t {
    mem::size_of::<CPassacreContext>() as ::libc::size_t
}

#[no_mangle]
pub extern "C" fn passacre_ctx_align() -> ::libc::size_t {
    mem::align_of::<CPassacreContext>() as ::libc::size_t
}

macro_rules! c_int_error {
    ($body:block) => {
        match (move || $body)() {
            Ok(()) => 0,
            Err(e) => PassacreError::to_c_int(&e),
        }
    };
}

macro_rules! c_export {
    ($name:ident, $(mut)* $ctx:tt, ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        #[no_mangle]
        #[allow(unused_mut)]
        pub extern "C" fn $name( ctx: *mut CPassacreContext $(, $arg : $argtype)* ) -> ::libc::c_int {
            c_int_error! {{
                let ctx = resolve_ptr!(null_check_mut, ctx, false);
                $($preamble)*
                match catch_unwind({
                    let $ctx = &ctx;
                    move || $body
                }) {
                    Ok(r) => r,
                    Err(_) => {
                        LAST_PANIC.with(|opt_ref| {
                            ctx.0.lock().unwrap().last_panic = opt_ref.borrow_mut().take();
                        });
                        Err(Panic.to_error())
                    },
                }
            }}
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


#[no_mangle]
pub extern "C" fn passacre_ctx_init(ctx: *mut CPassacreContext, allocator_fn: AllocatorFn) -> ::libc::c_int {
    c_int_error! {{
        let ctx = resolve_ptr!(null_check_mut, ctx, false);
        install_panic_hook();
        let p = CPassacreContext(sync::Mutex::new(Context::new(allocator_fn)));
        unsafe { ptr::write(ctx, p); }
        Ok(())
    }}
}

c_export!(passacre_ctx_describe_last_panic, ctx, (closure: *const ::libc::c_void), {}, {
    let mut ctx = try!(ctx.0.lock());
    if let Some(info) = ctx.last_panic.take() {
        try!(ctx.string_copy(closure, info.payload));
    }
    Ok(())
});

#[no_mangle]
pub extern "C" fn passacre_ctx_finished(ctx: *mut CPassacreContext) {
    if !ctx.is_null() {
        unsafe { drop_ptr(ctx); }
    }
}

#[repr(C)]
pub struct CMultiBase(sync::Mutex<MultiBase>);

macro_rules! passacre_mb_export {
    ($name:ident, $ctx:tt, $mb:ident, $null_allowed:expr,
     ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        c_export!($name, $ctx, ( mb: *const CMultiBase $(,$arg : $argtype)* ), {
            let mb_mutex = resolve_ptr!(null_check, mb, $null_allowed);
            $($preamble)*
        }, {
            let mut $mb = try!(mb_mutex.0.lock());
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

c_export!(passacre_mb_init, _, (mb: *mut CMultiBase), {}, {
    let p = CMultiBase(sync::Mutex::new(MultiBase::new()));
    unsafe { ptr::write(mb, p); }
    Ok(())
});

passacre_mb_export!(passacre_mb_required_bytes, _, mb, false, (dest: *mut ::libc::size_t), {
    let mut dest = AssertUnwindSafe(resolve_ptr!(null_check_mut, dest, false));
}, {
    let ret = mb.required_bytes();
    **dest = ret as ::libc::size_t;
    Ok(())
});

passacre_mb_export!(passacre_mb_entropy_bits, _, mb, false, (dest: *mut ::libc::size_t), {
    let mut dest = AssertUnwindSafe(resolve_ptr!(null_check_mut, dest, false));
}, {
    let ret = mb.entropy_bits();
    **dest = ret as ::libc::size_t;
    Ok(())
});

passacre_mb_export!(passacre_mb_enable_shuffle, _, mb, false, (), {}, {
    mb.enable_shuffle();
    Ok(())
});

passacre_mb_export!(passacre_mb_add_base, _, mb, false, (
    which: ::libc::c_uint, string: *const u8, string_length: ::libc::size_t), {
    recompose!(string, string_length);
}, {
    let base = try!(Base::of_c_parts(which, string));
    mb.add_base(base)
});

c_export!(passacre_mb_add_sub_mb, _, (parent: *const CMultiBase, child: *const CMultiBase), {
    if parent == child {
        fail!(UserError);
    }
    let parent = resolve_ptr!(null_check, parent, false);
    let child = resolve_ptr!(null_check, child, false);
}, {
    let mut parent = try!(parent.0.lock());
    let child = try!(child.0.lock());
    parent.add_base(Base::NestedBase(child.clone()))
});

passacre_mb_export!(passacre_mb_load_words_from_path, _, mb, false,
                    (path: *const u8, path_length: ::libc::size_t), {
    recompose!(path, path_length);
}, {
    // XXX: better error handling
    let path = path::Path::new(str::from_utf8(path).unwrap());
    mb.load_words_from_path(path)
});

passacre_mb_export!(passacre_mb_encode_from_bytes, ctx, mb, false,
                    (input: *const u8, input_length: ::libc::size_t,
                     closure: *const ::libc::c_void), {
    recompose!(input, input_length);
}, {
    let ctx = try!(ctx.0.lock());
    let ret = try!(mb.encode_from_bytes(input));
    try!(ctx.string_copy(closure, ret));
    Ok(())
});

#[no_mangle]
pub extern "C" fn passacre_mb_finished(mb: *mut CMultiBase) {
    if !mb.is_null() {
        unsafe { drop_ptr(mb); }
    }
}


#[repr(C)]
pub struct CPassacreGenerator(sync::Mutex<PassacreGenerator<'static>>);

macro_rules! passacre_gen_export {
    ($name:ident, $ctx:tt, $gen:ident, $null_allowed:expr,
     ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        c_export!($name, $ctx, ( gen: *const CPassacreGenerator $(,$arg : $argtype)* ), {
            let gen_mutex = resolve_ptr!(null_check, gen, $null_allowed);
            $($preamble)*
        }, {
            let mut $gen = try!(gen_mutex.0.lock());
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


c_export!(passacre_gen_init, _, (gen: *mut CPassacreGenerator, algorithm: ::libc::c_uint), {}, {
    testing_panic!(algorithm == 99);
    let algorithm = try!(Algorithm::of_c_uint(algorithm));
    let p = try!(PassacreGenerator::new(algorithm));
    let p = CPassacreGenerator(sync::Mutex::new(p));
    unsafe { ptr::write(gen, p); }
    Ok(())
});

passacre_gen_export!(passacre_gen_use_scrypt, _, gen, false,
                     (n: u64, r: u32, p: u32, persistence_buffer: *mut u8), {
    let buf = try!(null_check_mut(persistence_buffer as *mut [u8; SCRYPT_BUFFER_SIZE], true));
    let kdf = Kdf::new_scrypt(n, r, p, buf);
}, {
    gen.use_kdf(kdf)
});


passacre_gen_export!(passacre_gen_absorb_username_password_site, _, gen, false,
                     (username: *const ::libc::c_uchar, username_length: ::libc::size_t,
                      password: *const ::libc::c_uchar, password_length: ::libc::size_t,
                      site: *const ::libc::c_uchar, site_length: ::libc::size_t), {
    recompose!(username, username_length);
    recompose!(password, password_length);
    recompose!(site, site_length);
}, {
    gen.absorb_username_password_site(username, password, site)
});


passacre_gen_export!(passacre_gen_absorb_null_rounds, _, gen, false,
                     (n_rounds: ::libc::size_t), {}, {
    gen.absorb_null_rounds(n_rounds as usize)
});


passacre_gen_export!(passacre_gen_squeeze, _, gen, false,
                     (output: *mut ::libc::c_uchar, output_length: ::libc::size_t), {
    recompose!(mut output, output_length);
}, {
    gen.squeeze(&mut *output)
});

passacre_gen_export!(passacre_gen_squeeze_password, ctx, gen, false,
                     (mb: *const CMultiBase, closure: *const ::libc::c_void), {
    let mb = resolve_ptr!(null_check, mb, false);
}, {
    let ctx = try!(ctx.0.lock());
    let mut mb = try!(mb.0.lock());
    ctx.string_copy(closure, try!(mb.encode_from_generator(&mut *gen)))
});


#[no_mangle]
pub extern "C" fn passacre_gen_finished(gen: *mut CPassacreGenerator) {
    if !gen.is_null() {
        unsafe { drop_ptr(gen); }
    }
}


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

impl<'a> UnwindSafe for ByteCopier<'a> {}


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
                    "unknown panic"
                },
                Some(e) => e.to_string(),
                None => "unknown error",
            };
            copier.copy(err_str.as_bytes());
            copier
        };
        catch_unwind(closure)
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
