/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![feature(set_stdio)]
#![feature(std_misc)]

extern crate libc;

mod util;
mod deps;
mod passacre;
pub mod c;
pub use ::passacre::{Algorithm, PassacreGenerator, SCRYPT_BUFFER_SIZE};
