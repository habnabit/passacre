/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

macro_rules! fail {
    ($expr:expr) => {
        return Err(::std::convert::From::from($expr))
    };
}

macro_rules! testing_panic {
    ($cond:expr) => {{
        if cfg!(feature = "testing-checks") && $cond {
            panic!("testing panic");
        }
    }};
}

macro_rules! testing_fail {
    ($cond:expr, $result:expr) => {{
        if cfg!(feature = "testing-checks") && $cond {
            fail!($result);
        }
    }};
}

mod deps;
pub mod error;
mod multibase;
mod passacre;
#[cfg(feature = "python")]
mod python;
pub use crate::error::PassacreError;
pub use crate::multibase::{Base, MultiBase};
pub use crate::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
