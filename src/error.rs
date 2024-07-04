/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::io;

#[cfg(feature = "python")]
use pyo3::PyErr;

#[derive(thiserror::Error, Debug)]
pub enum PassacreError {
    #[error("panic")]
    Panic,
    #[error("keccak error")]
    KeccakError,
    #[error("skein error")]
    SkeinError,
    #[error("scrypt error")]
    ScryptError,
    #[error("user error")]
    UserError,
    #[error("internal error")]
    InternalError,
    #[error("domain error")]
    DomainError,
    #[error("allocator error")]
    AllocatorError,
    #[error("mutex error")]
    MutexError,
    #[error("IO error {0:#?}")]
    IO(#[from] io::Error),
    #[cfg(feature = "python")]
    #[error("python error {0:#?}")]
    Python(#[from] PyErr),
}

pub type PassacreResult<T> = Result<T, PassacreError>;
#[cfg(feature = "python")]
pyo3::create_exception!(
    passacre_backend,
    PassacreException,
    pyo3::exceptions::PyException
);

#[cfg(feature = "python")]
impl Into<PyErr> for PassacreError {
    fn into(self) -> PyErr {
        match self {
            PassacreError::Python(p) => p,
            s => PassacreException::new_err(format!("error: {:#?}", s)),
        }
    }
}
