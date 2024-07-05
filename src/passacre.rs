/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use bytes::{BufMut, BytesMut};
use rand::RngCore;
use skein::{Skein512, Digest};
use threefish::Threefish512;
use tiny_keccak_1536::{Hasher, NonstandardShake1536, Xof};

use crate::error::{PassacreError::*, PassacreResult};

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
    Scrypt(scrypt::Params),
}

impl Kdf {
    pub fn new_scrypt(n: u64, r: u32, p: u32) -> PassacreResult<Kdf> {
        let log_n = (n as f64).log2() as u8;
        let params = scrypt::Params::new(log_n, r, p, SCRYPT_BUFFER_SIZE).map_err(|_| UserError)?;
        Ok(Kdf::Scrypt(params))
    }

    pub fn derive(&self, username: &[u8], password: &[u8]) -> PassacreResult<Vec<u8>> {
        match self {
            Kdf::Scrypt(params) => {
                testing_fail!(params.log_n() == 99 && params.r() == 99 && params.p() == 99, ScryptError);
                let mut ret = vec![0u8; SCRYPT_BUFFER_SIZE];
                scrypt::scrypt(password, username, params, &mut ret).map_err(|_| InternalError)?;
                Ok(ret)
            }
        }
    }
}

const SKEIN_512_BLOCK_BYTES: usize = 64;

struct SkeinPrng {
    threefish: threefish::Threefish512,
    buffer: BytesMut,
}

enum HashState {
    Keccak(NonstandardShake1536),
    Skein(Skein512),
    SkeinPrng(SkeinPrng),
}

impl HashState {
    fn of_algorithm(algorithm: &Algorithm) -> PassacreResult<HashState> {
        let hash_state = match algorithm {
            &Algorithm::Keccak => HashState::Keccak(NonstandardShake1536::new()),
            &Algorithm::Skein => {
                let mut hash: Skein512 = Default::default();
                let nulls = [0u8; SKEIN_512_BLOCK_BYTES];
                hash.update(&nulls);
                HashState::Skein(hash)
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

pub const SCRYPT_BUFFER_SIZE: usize = 64;

const DELIMITER: &'static [u8] = b":";
const TWEAK: [u8; 16] = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x3f,
];
const ONE_IN_64: [u8; 64] = [
    1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
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
        match &mut self.hash_state {
            HashState::Keccak(sponge) => sponge.update(input),
            HashState::Skein(skein) => skein.update(input),
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
        let new_state = if let HashState::Skein(skein) = &mut self.hash_state {
            use skein::Digest;
            let hash = skein.finalize_reset();
            let threefish = Threefish512::new_with_tweak(&hash.into(), &TWEAK);
            let mut buffer: BytesMut = Default::default();
            buffer.reserve(64);
            Some(HashState::SkeinPrng(SkeinPrng { buffer, threefish }))
        } else {
            None
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
        match &mut self.hash_state {
            HashState::Keccak(sponge) => {
                sponge.squeeze(output);
            },
            HashState::SkeinPrng(skein) => {
                let mut n_bytes = output.len();
                let mut output_pos = 0usize;
                while n_bytes > 0 {
                    if skein.buffer.is_empty() {
                        let mut next_state = [0u64; 8];
                        skein.threefish.encrypt_block_u64(&mut next_state);
                        let mut next_buffer: [u64; 8] = bytemuck::cast(ONE_IN_64);
                        skein.threefish.encrypt_block_u64(&mut next_buffer);
                        skein.buffer.put(bytemuck::cast_slice(&next_buffer));
                        let next_state_bytes: [u8; 64] = bytemuck::cast(next_state);
                        skein.threefish = Threefish512::new_with_tweak(&next_state_bytes, &TWEAK);
                    }
                    let splut = skein.buffer.split_to(n_bytes.min(skein.buffer.len()));
                    let copied = copy_from_shorter_slice(
                        &mut output[output_pos..],
                        &splut,
                    );
                    n_bytes -= copied;
                    output_pos += copied;
                }
                output.reverse();
            }
            _ => unreachable!(),
        }
        Ok(())
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
