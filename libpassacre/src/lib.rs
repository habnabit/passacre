/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![feature(convert)]
#![feature(set_stdio)]
#![feature(std_misc)]
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
pub use ::passacre::{Algorithm, PassacreGenerator, SCRYPT_BUFFER_SIZE};
pub use ::multibase::{Base, MultiBase};
