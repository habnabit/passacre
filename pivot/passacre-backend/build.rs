/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

extern crate capnpc;

fn main() {
    println!("cargo:rustc-link-search={}", env!("CMAKE_BINARY_DIR"));
    ::capnpc::CompilerCommand::new().file("passacre.capnp").run().unwrap();
}
