/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![feature(set_stdio, ptr_as_ref, catch_panic)]

extern crate libc;

mod util;
mod deps;
mod passacre;
pub mod c;
pub use ::passacre::{Algorithm, Kdf, PassacreGenerator, SCRYPT_BUFFER_SIZE};
