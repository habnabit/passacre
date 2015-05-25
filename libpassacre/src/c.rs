/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::{mem, ptr, slice};

use ::passacre::{Algorithm, PassacreGenerator};


macro_rules! c_export {
    ($name:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        #[no_mangle]
        pub extern "C" fn $name( $($arg : $argtype,)* ) -> ::libc::c_int {
            let closure = move || $body;
            match closure() {
                Ok(()) => 0,
                Err(()) => -1,
            }
        }
    };
}

macro_rules! passacre_gen_export {
    ($name:ident, $gen:ident, ( $($arg:ident : $argtype:ty),* ), $body:block) => {
        c_export!($name, ( gen: *mut PassacreGenerator $(,$arg : $argtype)* ), {
            if gen.is_null() {
                return Err(());
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
pub extern "C" fn passacre_gen_scrypt_buffer_size() -> ::libc::size_t{
    64
}

c_export!(passacre_gen_init, (gen: *mut PassacreGenerator, algorithm: ::libc::c_uint), {
    let algorithm = try!(Algorithm::of_c_uint(algorithm));
    let p = try!(PassacreGenerator::new(algorithm));
    unsafe { ptr::write(gen, p); }
    Ok(())
});

passacre_gen_export!(passacre_gen_use_scrypt, gen, (n: u64, r: u32, p: u32,
                                                    persistence_buffer: *mut u8), {
    let persistence_buffer = if persistence_buffer.is_null() {
        None
    } else {
        Some(persistence_buffer)
    };
    gen.use_scrypt(n, r, p, persistence_buffer)
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

#[no_mangle]
pub extern "C" fn passacre_gen_finished(gen: *mut PassacreGenerator) {
    if gen.is_null() {
        return;
    }
    mem::drop(unsafe { &mut *gen });
}
