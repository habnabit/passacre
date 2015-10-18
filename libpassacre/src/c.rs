/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, ptr, slice, str, io};
use std::cell::RefCell;
use std::thread::catch_panic;

use ::passacre::{Algorithm, Kdf, PassacreError, PassacreGenerator, SCRYPT_BUFFER_SIZE};
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


macro_rules! force_block {
    ($b:block) => ($b);
}

macro_rules! c_export {
    ($name:ident, ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        #[no_mangle]
        #[allow(unused_mut)]
        pub extern "C" fn $name( $($arg : $argtype,)* ) -> ::libc::c_int {
            let closure_result = force_block!({
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
                catch_panic(closure)
            });
            let ret = match closure_result {
                Ok(Ok(())) => None,
                Ok(Err(e)) => Some(e),
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
    ($name:ident, $gen:ident, ( $($arg:ident : $argtype:ty),* ), { $($preamble:tt)* }, $body:block) => {
        c_export!($name, ( gen: *mut PassacreGenerator<'static> $(,$arg : $argtype)* ), {
            let mut $gen = match unsafe { gen.as_mut() } {
                None => return PassacreError::UserError.to_c_int(),
                Some(gen) => gen,
            };
            $($preamble)*
        }, $body);
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

passacre_gen_export!(passacre_gen_init, gen, (algorithm: ::libc::c_uint), {}, {
    let algorithm = try!(Algorithm::of_c_uint(algorithm));
    let p = try!(PassacreGenerator::new(algorithm));
    unsafe { ptr::write(gen, p); }
    Ok(())
});

passacre_gen_export!(passacre_gen_use_scrypt, gen, (n: u64, r: u32, p: u32,
                                                    persistence_buffer: *mut u8), {
    let buf = if persistence_buffer.is_null() {
        None
    } else {
        let buf = persistence_buffer as *mut [u8; SCRYPT_BUFFER_SIZE];
        Some(unsafe { &mut *buf })
    };
    let kdf = Kdf::new_scrypt(n, r, p, buf);
}, {
    gen.use_kdf(kdf)
});


passacre_gen_export!(passacre_gen_absorb_username_password_site, gen, (
    username: *const ::libc::c_uchar, username_length: ::libc::size_t,
    password: *const ::libc::c_uchar, password_length: ::libc::size_t,
    site: *const ::libc::c_uchar, site_length: ::libc::size_t), {
    let username = unsafe { slice::from_raw_parts(username, username_length as usize) };
    let password = unsafe { slice::from_raw_parts(password, password_length as usize) };
    let site = unsafe { slice::from_raw_parts(site, site_length as usize) };
}, {
    gen.absorb_username_password_site(username, password, site)
});


passacre_gen_export!(passacre_gen_absorb_null_rounds, gen, (n_rounds: ::libc::size_t), {}, {
    gen.absorb_null_rounds(n_rounds as usize)
});


passacre_gen_export!(passacre_gen_squeeze, gen, (output: *mut ::libc::c_uchar, output_length: ::libc::size_t), {
    let output = unsafe { slice::from_raw_parts_mut(output, output_length as usize) };
}, {
    gen.squeeze(output)
});

c_export!(passacre_gen_finished, (gen: *const PassacreGenerator<'static>), {
    let gen = match unsafe { gen.as_ref() } {
        // leaky abstraction, sadly. fixme maybe?
        None => return 0,
        Some(gen) => gen,
    };
}, {
    // read the pointer and do nothing with the result, so that the value
    // immediately goes out of scope and is dropped. you can't move a value out
    // of dereferencing a *mut, and passing a &mut to mem::drop is a no-op.
    unsafe { ptr::read(gen); }
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


#[no_mangle]
pub extern "C" fn passacre_error(which: ::libc::c_int, dest_p: *mut ::libc::c_uchar, dest_length: ::libc::size_t)
                                 -> ::libc::size_t {
    let mut copier = ByteCopier::new(dest_p, dest_length as usize);
    let closure_result = {
        let closure = move || {
            let err = PassacreError::of_c_int(which);
            let err_str = match err {
                Some(PassacreError::Panic) => {
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
        catch_panic(closure)
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
