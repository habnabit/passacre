/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, ptr, slice, str, io};
use std::cell::RefCell;
use std::rt::unwind::try;

use ::passacre::{Algorithm, PassacreError, PassacreGenerator, SCRYPT_BUFFER_SIZE};
use ::util::clone_from_slice;


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

c_export!(passacre_gen_finished, (gen: *mut PassacreGenerator), {
    if gen.is_null() {
        return Ok(());
    }
    // read the pointer and do nothing with the result, so that the value
    // immediately goes out of scope and is dropped. you can't move a value out
    // of dereferencing a *mut, and passing a &mut to mem::drop is a no-op.
    unsafe { ptr::read(gen); }
    Ok(())
});

#[no_mangle]
pub extern "C" fn passacre_error(which: ::libc::c_int, dest: *mut ::libc::c_uchar, dest_length: ::libc::size_t)
                                 -> ::libc::size_t {
    let err = PassacreError::of_c_int(which);
    let dest = unsafe { slice::from_raw_parts_mut(dest, dest_length as usize) };
    let err_str = match err {
        Some(PassacreError::Panic) => {
            let mut copied = None;
            ERROR_STRING.with(|err_string| {
                let err_string = err_string.borrow();
                if err_string.is_empty() {
                    return;
                }
                copied = Some(clone_from_slice(dest, err_string.as_bytes()));
            });
            match copied {
                Some(count) => return count as ::libc::size_t,
                None => "unknown panic",
            }
        },
        Some(e) => e.to_string(),
        None => "unknown error",
    };
    clone_from_slice(dest, err_str.as_bytes()) as ::libc::size_t
}
