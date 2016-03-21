/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![feature(set_stdio, recover)]
#![cfg_attr(test, feature(plugin))]
#![cfg_attr(test, plugin(fnconcat))]

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

pub mod error;
mod util;
mod deps;
mod multibase;
mod passacre;
pub mod c;
pub use ::error::PassacreError;
pub use ::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
pub use ::multibase::{Base, MultiBase};
