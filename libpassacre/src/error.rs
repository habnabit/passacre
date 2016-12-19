/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![macro_use]

use std::{io, sync};

use self::PassacreErrorKind::*;


macro_rules! fail {
    ($expr:expr) => (
        return Err(::std::convert::From::from($expr));
    )
}

#[derive(Debug)]
pub struct Nonequal<T>(pub T);

impl<T> PartialEq for Nonequal<T> {
    fn eq(&self, _: &Self) -> bool { false }
}

#[derive(Debug, PartialEq)]
pub enum PassacreErrorKind {
    Panic,
    KeccakError,
    SkeinError,
    ScryptError,
    UserError,
    InternalError,
    DomainError,
    AllocatorError,
    MutexError,
    Capnp(Nonequal<::capnp::Error>),
    IO(Nonequal<io::Error>),
}

impl PassacreErrorKind {
    pub fn to_error(self) -> PassacreError {
        PassacreError { kind: self, context: None }
    }
}

#[derive(Debug, PartialEq)]
pub struct PassacreError {
    pub kind: PassacreErrorKind,
    context: Option<String>,
}

impl PassacreError {
    pub fn to_string(&self) -> &'static str {
        match self.kind {
            Panic => "panic",
            KeccakError => "keccak error",
            SkeinError => "skein error",
            ScryptError => "scrypt error",
            UserError => "user error",
            InternalError => "internal error",
            DomainError => "domain error",
            AllocatorError => "allocator error",
            MutexError => "mutex error",
            Capnp(_) => "capnp error",
            IO(_) => "IO error",
        }
    }
}

pub type PassacreResult<T> = Result<T, PassacreError>;


impl From<PassacreErrorKind> for PassacreError {
    fn from(kind: PassacreErrorKind) -> PassacreError {
        kind.to_error()
    }
}

impl From<(PassacreErrorKind, &'static str)> for PassacreError {
    fn from((kind, context): (PassacreErrorKind, &'static str)) -> PassacreError {
        PassacreError { kind: kind, context: Some(context.to_string()) }
    }
}

impl<T> From<sync::PoisonError<T>> for PassacreError {
    fn from(_: sync::PoisonError<T>) -> PassacreError {
        PassacreError { kind: MutexError, context: None }
    }
}

impl From<::capnp::Error> for PassacreError {
    fn from(e: ::capnp::Error) -> PassacreError {
        PassacreErrorKind::Capnp(Nonequal(e)).into()
    }
}

impl From<::capnp::NotInSchema> for PassacreError {
    fn from(e: ::capnp::NotInSchema) -> PassacreError {
        e.into()
    }
}

impl From<io::Error> for PassacreError {
    fn from(e: io::Error) -> PassacreError {
        PassacreErrorKind::IO(Nonequal(e)).into()
    }
}

impl Into<::capnp::Error> for PassacreError {
    fn into(self) -> ::capnp::Error {
        if let PassacreErrorKind::Capnp(e) = self.kind {
            e.0
        } else {
            // XXX: information leakage?
            ::capnp::Error::failed(format!("passacre internal error: {:?}", self))
        }
    }
}
