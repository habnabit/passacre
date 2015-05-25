/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

fn main() {
    println!("cargo:rustc-link-search={}", env!("CMAKE_BINARY_DIR"));
}
