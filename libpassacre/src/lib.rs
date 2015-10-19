/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![feature(convert, set_stdio, catch_panic)]
#![cfg_attr(test, feature(plugin))]
#![cfg_attr(test, plugin(fnconcat))]

extern crate libc;
extern crate ramp;

pub mod error;
mod util;
mod deps;
mod multibase;
mod passacre;
pub mod c;
pub use ::error::PassacreError;
pub use ::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
pub use ::multibase::{Base, MultiBase};
