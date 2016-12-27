/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![cfg_attr(test, feature(plugin))]
#![cfg_attr(test, plugin(fnconcat))]

extern crate capnp;
#[macro_use] extern crate gj;
extern crate libc;
extern crate ramp;
extern crate rand;

macro_rules! testing_panic {
    ($cond:expr) => {{
        if cfg!(feature = "testing-checks") && $cond {
            panic!("testing panic");
        }
    }}
}

macro_rules! testing_fail {
    ($cond:expr, $result:expr) => {{
        if cfg!(feature = "testing-checks") && $cond {
            fail!($result);
        }
    }}
}

pub mod passacre_capnp {
  include!(concat!(env!("OUT_DIR"), "/passacre_capnp.rs"));
}

pub mod error;
pub mod rpc;
mod deps;
mod multibase;
mod passacre;
pub mod wordlists;
pub use ::error::PassacreError;
pub use ::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
pub use ::multibase::{Base, MultiBase};
