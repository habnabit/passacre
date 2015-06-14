/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::mem::uninitialized;
use std::slice;

use ::error::PassacreErrorKind::*;
use ::error::PassacreResult;
use ::util::{set_memory, clone_from_slice};


macro_rules! decompose {
    ($name:ident) => {
        let $name = ($name.as_ptr(), $name.len() as ::libc::size_t);
    };
    (mut $name:ident) => {
        let $name = ($name.as_mut_ptr(), $name.len() as ::libc::size_t);
    };
}

macro_rules! check_eq {
    ($expected:expr, $err:expr, $actual:expr) => {{
        if $expected != $actual {
            fail!($err);
        }
    }};
}

macro_rules! check_skein {
    ($actual:expr) => { check_eq!(::deps::SKEIN_SUCCESS, SkeinError, $actual); };
}


pub enum Algorithm {
    Keccak,
    Skein,
}

impl Algorithm {
    pub fn of_c_uint(which: ::libc::c_uint) -> PassacreResult<Algorithm> {
        let result = match which {
            0 => Algorithm::Keccak,
            1 => Algorithm::Skein,
            _ => fail!(UserError),
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

const SKEIN_512_BLOCK_BYTES: usize = 64;

struct SkeinPrng {
    threefish: ::deps::ThreefishKey_t,
    buffer: [u8; SKEIN_512_BLOCK_BYTES],
    bytes_remaining: usize,
}

enum HashState {
    Keccak(*mut ::deps::spongeState),
    Skein(::deps::SkeinCtx_t),
    SkeinPrng(SkeinPrng),
}

const SPONGE_RATE: ::libc::c_uint = 64;
const SPONGE_CAPACITY: ::libc::c_uint = 1536;

impl HashState {
    fn of_algorithm(algorithm: &Algorithm) -> PassacreResult<HashState> {
        let hash_state = match algorithm {
            &Algorithm::Keccak => unsafe {
                let sponge = ::deps::AllocSponge();
                if sponge.is_null() {
                    fail!(KeccakError);
                }
                if ::deps::InitSponge(sponge, SPONGE_RATE, SPONGE_CAPACITY) != 0 {
                    ::deps::FreeSponge(sponge);
                    fail!(KeccakError);
                }
                HashState::Keccak(sponge)
            },
            &Algorithm::Skein => unsafe {
                let mut skein: ::deps::SkeinCtx_t = uninitialized();
                check_skein!(::deps::skeinCtxPrepare(&mut skein, ::deps::Skein512));
                check_skein!(::deps::skeinInit(&mut skein, ::deps::Skein512));
                let nulls = [0u8; SKEIN_512_BLOCK_BYTES];
                decompose!(nulls);
                check_skein!(::deps::skeinUpdate(&mut skein, nulls.0, nulls.1));
                HashState::Skein(skein)
            },
        };
        Ok(hash_state)
    }
}

impl Drop for HashState {
    fn drop(&mut self) {
        match self {
            &mut HashState::Keccak(sponge) => unsafe {
                ::deps::FreeSponge(sponge);
            },
            _ => (),
        }
    }
}

pub struct PassacreGenerator {
    state: State,
    kdf: Option<Kdf>,
    hash_state: HashState,
}

pub const SCRYPT_BUFFER_SIZE: usize = 64;

fn with_persistence_buffer<F>(buf: Option<*mut u8>, func: F) where F: FnOnce(&mut [u8]) {
    match buf {
        Some(buf) => {
            let target = unsafe { slice::from_raw_parts_mut(buf, SCRYPT_BUFFER_SIZE) };
            func(target);
        },
        None => (),
    }
}

const DELIMITER: &'static [u8] = b":";
const TWEAK: [u8; 24] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x3f, 0, 0, 0, 0, 0, 0, 0, 0];

impl PassacreGenerator {
    pub fn new(algorithm: Algorithm) -> PassacreResult<PassacreGenerator> {
        let p = PassacreGenerator {
            state: State::Initialized,
            kdf: None,
            hash_state: try!(HashState::of_algorithm(&algorithm)),
        };
        Ok(p)
    }

    pub fn use_scrypt(&mut self, n: u64, r: u32, p: u32, persistence_buffer: Option<*mut u8>)
                      -> PassacreResult<()> {
        match self.state {
            State::Initialized => (),
            _ => fail!(UserError),
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

    fn absorb(&mut self, input: &[u8]) -> PassacreResult<()> {
        decompose!(input);
        match self.hash_state {
            HashState::Keccak(sponge) => unsafe {
                check_eq!(0, KeccakError,
                          ::deps::Absorb(sponge, input.0, input.1 * 8));
            },
            HashState::Skein(ref mut skein) => unsafe {
                check_skein!(::deps::skeinUpdate(skein, input.0, input.1));
            },
            _ => fail!(InternalError),
        }
        Ok(())
    }

    pub fn absorb_username_password_site(&mut self, username: &[u8], password: &[u8], site: &[u8])
                                         -> PassacreResult<()> {
        match self.state {
            State::Initialized | State::KdfSelected => (),
            _ => fail!(UserError),
        }
        match self.kdf {
            Some(Kdf::Scrypt{ n, r, p, persistence_buffer }) => unsafe {
                let mut scrypt_result: [u8; SCRYPT_BUFFER_SIZE] = uninitialized();
                {
                    decompose!(username);
                    decompose!(password);
                    decompose!(mut scrypt_result);
                    check_eq!(0, ScryptError,
                              ::deps::crypto_scrypt(password.0, password.1, username.0, username.1,
                                                    n, r, p, scrypt_result.0, scrypt_result.1));
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

    pub fn absorb_null_rounds(&mut self, n_rounds: usize) -> PassacreResult<()> {
        match self.state {
            State::AbsorbedPassword | State::AbsorbedNulls => (),
            _ => fail!(UserError),
        }
        let nulls = [0u8; 1024];
        for _ in 0..n_rounds {
            try!(self.absorb(&nulls));
        }
        self.state = State::AbsorbedNulls;
        Ok(())
    }

    pub fn squeeze(&mut self, output: &mut [u8]) -> PassacreResult<()> {
        match self.state {
            State::AbsorbedPassword | State::AbsorbedNulls => {
                self.state = State::Squeezing;
            },
            State::Squeezing => (),
            _ => fail!(UserError),
        }
        let new_state = match self.hash_state {
            HashState::Skein(ref mut skein) => unsafe {
                let mut hash: [u8; SKEIN_512_BLOCK_BYTES] = uninitialized();
                check_skein!(::deps::skeinFinal(skein, hash.as_mut_ptr()));
                let mut threefish: ::deps::ThreefishKey_t = uninitialized();
                ::deps::threefishSetKey(&mut threefish, ::deps::Threefish512,
                                        hash.as_ptr() as *const u64, TWEAK.as_ptr() as *const u64);
                Some(HashState::SkeinPrng(SkeinPrng {
                    threefish: threefish,
                    buffer: [0u8; SKEIN_512_BLOCK_BYTES],
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

    fn really_squeeze(&mut self, output: &mut [u8]) -> PassacreResult<()> {
        match self.hash_state {
            HashState::Keccak(sponge) => unsafe {
                decompose!(mut output);
                check_eq!(0, KeccakError, ::deps::Squeeze(sponge, output.0, output.1 * 8));
                return Ok(());
            },
            HashState::SkeinPrng(ref mut prng) => unsafe {
                let mut n_bytes = output.len();
                let mut input = [0u8; SKEIN_512_BLOCK_BYTES];
                let mut output_pos = 0usize;
                while n_bytes > 0 {
                    if prng.bytes_remaining == 0 {
                        let mut state_output: [u8; SKEIN_512_BLOCK_BYTES] = uninitialized();
                        input[0] = 0;
                        ::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish, input.as_ptr(), state_output.as_mut_ptr());
                        input[0] = 1;
                        ::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish, input.as_ptr(), prng.buffer.as_mut_ptr());
                        ::deps::threefishSetKey(
                            &mut prng.threefish, ::deps::Threefish512,
                            state_output.as_ptr() as *const u64, TWEAK.as_ptr() as *const u64);
                        prng.bytes_remaining = prng.buffer.len();
                    }
                    let copied = clone_from_slice(
                        &mut output[output_pos..], &prng.buffer[prng.buffer.len() - prng.bytes_remaining..]);
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
