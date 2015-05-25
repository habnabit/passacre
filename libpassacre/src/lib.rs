/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

extern crate libc;

mod util;
mod deps;
mod passacre;
pub mod c;
pub use ::passacre::{Algorithm, PassacreGenerator, SCRYPT_BUFFER_SIZE};
