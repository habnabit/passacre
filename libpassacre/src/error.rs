/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#![macro_use]

use self::PassacreErrorKind::*;


macro_rules! fail {
    ($expr:expr) => (
        return Err(::std::convert::From::from($expr));
    )
}


#[derive(Clone, Copy, Debug, PartialEq)]
pub enum PassacreErrorKind {
    Panic,
    KeccakError,
    SkeinError,
    ScryptError,
    UserError,
    InternalError,
    DomainError,
    AllocatorError,
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
    pub fn of_c_int(which: ::libc::c_int) -> Option<PassacreError> {
        let result = match which {
            -1 => Panic,
            -2 => KeccakError,
            -3 => SkeinError,
            -4 => ScryptError,
            -5 => UserError,
            -6 => InternalError,
            -7 => DomainError,
            -8 => AllocatorError,
            _ => return None,
        };
        Some(result.to_error())
    }

    pub fn to_c_int(&self) -> ::libc::c_int {
        match self.kind {
            Panic => -1,
            KeccakError => -2,
            SkeinError => -3,
            ScryptError => -4,
            UserError => -5,
            InternalError => -6,
            DomainError => -7,
            AllocatorError => -8,
        }
    }

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
