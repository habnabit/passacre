/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::mem::uninitialized;
use std::slice;

use ::util::{set_memory, clone_from_slice};


pub enum Algorithm {
    Keccak,
    Skein,
}

impl Algorithm {
    pub fn of_c_uint(which: ::libc::c_uint) -> Result<Algorithm, ()> {
        let result = match which {
            0 => Algorithm::Keccak,
            1 => Algorithm::Skein,
            _ => return Err(()),
        };
        Ok(result)
    }
}

enum State {
    Initialized,
    KdfSelected,
    AbsorbedPassword,
    AbsorbedNulls,
    Squeezing,
}

enum Kdf {
    Scrypt {
        n: u64,
        r: u32,
        p: u32,
        persistence_buffer: Option<*mut u8>,
    },
}

struct SkeinPrng {
    threefish: ::deps::ThreefishKey_t,
    buffer: [u8; 64],
    bytes_remaining: usize,
}

enum HashState {
    Keccak(::deps::spongeState),
    Skein(::deps::SkeinCtx_t),
    SkeinPrng(SkeinPrng),
}

impl HashState {
    fn of_algorithm(algorithm: &Algorithm) -> Result<HashState, ()> {
        let hash_state = match algorithm {
            &Algorithm::Keccak => unsafe {
                let mut sponge: ::deps::spongeState = uninitialized();
                if ::deps::InitSponge(&mut sponge, 64, 1536) != 0 {
                    return Err(());
                }
                HashState::Keccak(sponge)
            },
            &Algorithm::Skein => unsafe {
                let mut skein: ::deps::SkeinCtx_t = uninitialized();
                if ::deps::skeinCtxPrepare(&mut skein, ::deps::Skein512) != ::deps::SKEIN_SUCCESS {
                    return Err(());
                }
                if ::deps::skeinInit(&mut skein, 512) != ::deps::SKEIN_SUCCESS {
                    return Err(());
                }
                let nulls = [0u8; 64];
                if ::deps::skeinUpdate(&mut skein, nulls.as_ptr(), 64) != ::deps::SKEIN_SUCCESS {
                    return Err(());
                }
                HashState::Skein(skein)
            },
        };
        Ok(hash_state)
    }
}

pub struct PassacreGenerator {
    state: State,
    kdf: Option<Kdf>,
    hash_state: HashState,
}

fn with_persistence_buffer<F>(buf: Option<*mut u8>, func: F) where F: FnOnce(&mut [u8]) {
    match buf {
        Some(buf) => {
            let target = unsafe { slice::from_raw_parts_mut(buf, 64) };
            func(target);
        },
        None => (),
    }
}

const DELIMITER: &'static [u8] = b":";
const TWEAK: [u8; 24] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x3f, 0, 0, 0, 0, 0, 0, 0, 0];

impl PassacreGenerator {
    pub fn new(algorithm: Algorithm) -> Result<PassacreGenerator, ()> {
        let p = PassacreGenerator {
            state: State::Initialized,
            kdf: None,
            hash_state: try!(HashState::of_algorithm(&algorithm)),
        };
        Ok(p)
    }

    pub fn use_scrypt(&mut self, n: u64, r: u32, p: u32, persistence_buffer: Option<*mut u8>) -> Result<(), ()> {
        match self.state {
            State::Initialized => (),
            _ => return Err(()),
        }
        self.kdf = Some(Kdf::Scrypt {
            n: n, r: r, p: p, persistence_buffer: persistence_buffer,
        });
        with_persistence_buffer(persistence_buffer, |target| {
            set_memory(target, b'x');
        });
        self.state = State::KdfSelected;
        Ok(())
    }

    fn absorb(&mut self, input: &[u8]) -> Result<(), ()> {
        match self.hash_state {
            HashState::Keccak(ref mut sponge) => unsafe {
                if ::deps::Absorb(sponge, input.as_ptr(), (input.len() * 8) as u64) != 0 {
                    return Err(());
                }
            },
            HashState::Skein(ref mut skein) => unsafe {
                if ::deps::skeinUpdate(skein, input.as_ptr(), input.len() as u64) != ::deps::SKEIN_SUCCESS {
                    return Err(());
                }
            },
            _ => return Err(()),
        }
        Ok(())
    }

    pub fn absorb_username_password_site(&mut self, username: &[u8], password: &[u8], site: &[u8]) -> Result<(), ()> {
        match self.state {
            State::Initialized | State::KdfSelected => (),
            _ => return Err(()),
        }
        match self.kdf {
            Some(Kdf::Scrypt{ n, r, p, persistence_buffer }) => unsafe {
                let mut scrypt_result: [u8; 64] = uninitialized();
                if ::deps::crypto_scrypt(password.as_ptr(), password.len() as u64,
                                         username.as_ptr(), username.len() as u64,
                                         n, r, p, scrypt_result.as_mut_ptr(), 64) != 0 {
                    return Err(());
                }
                try!(self.absorb(&scrypt_result));
                with_persistence_buffer(persistence_buffer, |target| {
                    clone_from_slice(target, &scrypt_result[..]);
                });
            },
            _ => {
                if !username.is_empty() {
                    try!(self.absorb(username));
                    try!(self.absorb(DELIMITER));
                }
                try!(self.absorb(password));
            }
        }
        try!(self.absorb(DELIMITER));
        try!(self.absorb(site));
        self.state = State::AbsorbedPassword;
        Ok(())
    }

    pub fn absorb_null_rounds(&mut self, n_rounds: usize) -> Result<(), ()> {
        match self.state {
            State::AbsorbedPassword | State::AbsorbedNulls => (),
            _ => return Err(()),
        }
        let nulls = [0u8; 1024];
        for _ in 0..n_rounds {
            try!(self.absorb(&nulls));
        }
        self.state = State::AbsorbedNulls;
        Ok(())
    }

    pub fn squeeze(&mut self, output: &mut [u8]) -> Result<(), ()> {
        match self.state {
            State::AbsorbedPassword | State::AbsorbedNulls => {
                self.state = State::Squeezing;
            },
            State::Squeezing => (),
            _ => return Err(()),
        }
        let new_state = match self.hash_state {
            HashState::Skein(ref mut skein) => unsafe {
                let mut hash: [u8; 64] = uninitialized();
                if ::deps::skeinFinal(skein, hash.as_mut_ptr()) != ::deps::SKEIN_SUCCESS {
                    return Err(());
                }
                let mut threefish: ::deps::ThreefishKey_t = uninitialized();
                ::deps::threefishSetKey(&mut threefish, ::deps::Threefish512,
                                        hash.as_ptr() as *const u64, TWEAK.as_ptr() as *const u64);
                Some(HashState::SkeinPrng(SkeinPrng {
                    threefish: threefish,
                    buffer: [0u8; 64],
                    bytes_remaining: 0,
                }))
            },
            _ => None,
        };
        match new_state {
            Some(new_state) => {
                self.hash_state = new_state;
            }
            None => (),
        }
        self.really_squeeze(output)
    }

    fn really_squeeze(&mut self, output: &mut [u8]) -> Result<(), ()> {
        match self.hash_state {
            HashState::Keccak(ref mut sponge) => unsafe {
                if ::deps::Squeeze(sponge, output.as_mut_ptr(), (output.len() * 8) as u64) != 0 {
                    return Err(());
                }
                return Ok(());
            },
            HashState::SkeinPrng(ref mut prng) => unsafe {
                let mut n_bytes = output.len();
                let mut input = [0u8; 64];
                let mut output_pos = 0usize;
                while n_bytes > 0 {
                    if prng.bytes_remaining == 0 {
                        let mut state_output: [u8; 64] = uninitialized();
                        input[0] = 0;
                        ::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish, input.as_ptr(), state_output.as_mut_ptr());
                        input[0] = 1;
                        ::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish, input.as_ptr(), prng.buffer.as_mut_ptr());
                        ::deps::threefishSetKey(
                            &mut prng.threefish, ::deps::Threefish512,
                            state_output.as_ptr() as *const u64, TWEAK.as_ptr() as *const u64);
                        prng.bytes_remaining = 64;
                    }
                    let copied = clone_from_slice(
                        &mut output[output_pos..], &prng.buffer[64 - prng.bytes_remaining..]);
                    prng.bytes_remaining -= copied;
                    n_bytes -= copied;
                    output_pos += copied;
                }
                output.reverse();
                Ok(())
            },
            _ => unreachable!(),
        }
    }
}
