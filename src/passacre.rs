/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use rand::RngCore;

use crate::error::{PassacreError::*, PassacreResult};

macro_rules! decompose {
    ($name:ident) => {
        decompose!($name as ::libc::size_t);
    };
    (mut $name:ident) => {
        decompose!(mut $name as ::libc::size_t);
    };
    ($name:ident as $typ:ty) => {
        let $name = ($name.as_ptr(), $name.len() as $typ);
    };
    (mut $name:ident as $typ:ty) => {
        let $name = ($name.as_mut_ptr(), $name.len() as $typ);
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
    ($actual:expr) => {
        check_eq!(crate::deps::SKEIN_SUCCESS, SkeinError, $actual);
    };
}

fn copy_from_shorter_slice<T: Copy>(dst: &mut [T], src: &[T]) -> usize {
    let ret = ::std::cmp::min(dst.len(), src.len());
    if ret > 0 {
        (&mut dst[..ret]).copy_from_slice(&src[..ret]);
    }
    ret
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

pub enum Kdf {
    Scrypt { n: u64, r: u32, p: u32 },
}

impl Kdf {
    pub fn new_scrypt(n: u64, r: u32, p: u32) -> Kdf {
        Kdf::Scrypt { n: n, r: r, p: p }
    }

    pub fn derive(&mut self, username: &[u8], password: &[u8]) -> PassacreResult<Vec<u8>> {
        match self {
            &mut Kdf::Scrypt { n, r, p } => {
                testing_fail!(n == 99 && r == 99 && p == 99, ScryptError);
                let mut scrypt_result = vec![0u8; SCRYPT_BUFFER_SIZE];
                {
                    decompose!(username);
                    decompose!(password);
                    decompose!(mut scrypt_result);
                    check_eq!(0, ScryptError, unsafe {
                        crate::deps::crypto_scrypt(
                            password.0,
                            password.1,
                            username.0,
                            username.1,
                            n,
                            r,
                            p,
                            scrypt_result.0,
                            scrypt_result.1,
                        )
                    });
                }
                Ok(scrypt_result)
            }
        }
    }
}

const SKEIN_512_BLOCK_BYTES: usize = 64;

struct SkeinPrng {
    threefish: crate::deps::ThreefishKey_t,
    buffer: [u8; SKEIN_512_BLOCK_BYTES],
    bytes_remaining: usize,
}

enum HashState {
    Keccak(*mut crate::deps::spongeState),
    Skein(crate::deps::SkeinCtx_t),
    SkeinPrng(SkeinPrng),
}

const SPONGE_RATE: ::libc::c_uint = 64;
const SPONGE_CAPACITY: ::libc::c_uint = 1536;

impl HashState {
    fn of_algorithm(algorithm: &Algorithm) -> PassacreResult<HashState> {
        let hash_state = match algorithm {
            &Algorithm::Keccak => unsafe {
                let sponge = crate::deps::AllocSponge();
                if sponge.is_null() {
                    fail!(KeccakError);
                }
                if crate::deps::InitSponge(sponge, SPONGE_RATE, SPONGE_CAPACITY) != 0 {
                    crate::deps::FreeSponge(sponge);
                    fail!(KeccakError);
                }
                HashState::Keccak(sponge)
            },
            &Algorithm::Skein => unsafe {
                let mut skein: crate::deps::SkeinCtx_t = Default::default();
                check_skein!(crate::deps::skeinCtxPrepare(
                    &mut skein,
                    crate::deps::Skein512
                ));
                check_skein!(crate::deps::skeinInit(&mut skein, crate::deps::Skein512));
                let nulls = [0u8; SKEIN_512_BLOCK_BYTES];
                decompose!(nulls);
                check_skein!(crate::deps::skeinUpdate(&mut skein, nulls.0, nulls.1));
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
                crate::deps::FreeSponge(sponge);
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

const DELIMITER: &'static [u8] = b":";
const TWEAK: [u8; 24] = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x3f, 0, 0, 0, 0, 0, 0, 0, 0,
];

impl PassacreGenerator {
    pub fn new(algorithm: Algorithm) -> PassacreResult<PassacreGenerator> {
        let p = PassacreGenerator {
            state: State::Initialized,
            kdf: None,
            hash_state: HashState::of_algorithm(&algorithm)?,
        };
        Ok(p)
    }

    pub fn use_kdf(&mut self, kdf: Kdf) -> PassacreResult<()> {
        match self.state {
            State::Initialized => (),
            _ => fail!(UserError),
        }
        self.kdf = Some(kdf);
        self.state = State::KdfSelected;
        Ok(())
    }

    fn absorb(&mut self, input: &[u8]) -> PassacreResult<()> {
        decompose!(input);
        match self.hash_state {
            HashState::Keccak(sponge) => unsafe {
                check_eq!(
                    0,
                    KeccakError,
                    crate::deps::Absorb(sponge, input.0, input.1 as ::libc::c_ulonglong * 8)
                );
            },
            HashState::Skein(ref mut skein) => unsafe {
                check_skein!(crate::deps::skeinUpdate(skein, input.0, input.1));
            },
            _ => fail!(InternalError),
        }
        Ok(())
    }

    pub fn absorb_username_password_site(
        &mut self,
        username: &[u8],
        password: &[u8],
        site: &[u8],
    ) -> PassacreResult<()> {
        match self.state {
            State::Initialized | State::KdfSelected => (),
            _ => fail!(UserError),
        }
        match self.kdf.as_mut().map(|kdf| kdf.derive(username, password)) {
            Some(Ok(kdf_derived)) => {
                self.absorb(&kdf_derived)?;
            }
            None => {
                if !username.is_empty() {
                    self.absorb(username)?;
                    self.absorb(DELIMITER)?;
                }
                self.absorb(password)?;
            }
            Some(Err(e)) => Err(e)?,
        };
        self.absorb(DELIMITER)?;
        self.absorb(site)?;
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
            self.absorb(&nulls)?;
        }
        self.state = State::AbsorbedNulls;
        Ok(())
    }

    pub fn squeeze(&mut self, output: &mut [u8]) -> PassacreResult<()> {
        match self.state {
            State::AbsorbedPassword | State::AbsorbedNulls => {
                self.state = State::Squeezing;
            }
            State::Squeezing => (),
            _ => fail!(UserError),
        }
        testing_panic!(output.len() == 99999);
        let new_state = match self.hash_state {
            HashState::Skein(ref mut skein) => unsafe {
                let mut hash = [0u8; SKEIN_512_BLOCK_BYTES];
                check_skein!(crate::deps::skeinFinal(skein, hash.as_mut_ptr()));
                let mut threefish: crate::deps::ThreefishKey_t = Default::default();
                crate::deps::threefishSetKey(
                    &mut threefish,
                    crate::deps::Threefish512,
                    hash.as_ptr() as *const u64,
                    TWEAK.as_ptr() as *const u64,
                );
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
                decompose!(mut output as ::libc::c_ulonglong);
                check_eq!(
                    0,
                    KeccakError,
                    crate::deps::Squeeze(sponge, output.0, output.1 * 8)
                );
                return Ok(());
            },
            HashState::SkeinPrng(ref mut prng) => unsafe {
                let mut n_bytes = output.len();
                let mut input = [0u8; SKEIN_512_BLOCK_BYTES];
                let mut output_pos = 0usize;
                while n_bytes > 0 {
                    if prng.bytes_remaining == 0 {
                        let mut state_output = [0u8; SKEIN_512_BLOCK_BYTES];
                        input[0] = 0;
                        crate::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish,
                            input.as_ptr(),
                            state_output.as_mut_ptr(),
                        );
                        input[0] = 1;
                        crate::deps::threefishEncryptBlockBytes(
                            &mut prng.threefish,
                            input.as_ptr(),
                            prng.buffer.as_mut_ptr(),
                        );
                        crate::deps::threefishSetKey(
                            &mut prng.threefish,
                            crate::deps::Threefish512,
                            state_output.as_ptr() as *const u64,
                            TWEAK.as_ptr() as *const u64,
                        );
                        prng.bytes_remaining = prng.buffer.len();
                    }
                    let copied = copy_from_shorter_slice(
                        &mut output[output_pos..],
                        &prng.buffer[prng.buffer.len() - prng.bytes_remaining..],
                    );
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

impl RngCore for PassacreGenerator {
    fn fill_bytes(&mut self, dest: &mut [u8]) {
        self.squeeze(dest).unwrap()
    }

    fn next_u32(&mut self) -> u32 {
        let mut ret = [0u8; 4];
        self.fill_bytes(&mut ret);
        u32::from_be_bytes(ret)
    }

    fn next_u64(&mut self) -> u64 {
        let mut ret = [0u8; 8];
        self.fill_bytes(&mut ret);
        u64::from_be_bytes(ret)
    }

    fn try_fill_bytes(&mut self, dest: &mut [u8]) -> Result<(), rand::Error> {
        self.squeeze(dest).map_err(|_| todo!())
    }
}
