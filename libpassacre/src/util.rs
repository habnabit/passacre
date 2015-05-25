// Copyright 2012-2014 The Rust Project Developers. See the COPYING
// file at the top-level directory of this distribution and at
// http://rust-lang.org/COPYRIGHT.
//
// Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
// http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
// <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
// option. This file may not be copied, modified, or distributed
// except according to those terms.

use std::{cmp, ptr};


pub fn set_memory(dst: &mut [u8], value: u8) {
    unsafe { ptr::write_bytes(dst.as_mut_ptr(), value, dst.len()) };
}

pub fn clone_from_slice<T>(dst: &mut [T], src: &[T]) -> usize where T: Clone {
    let min = cmp::min(dst.len(), src.len());
    let dst = &mut dst[.. min];
    let src = &src[.. min];
    for i in 0..min {
        dst[i].clone_from(&src[i]);
    }
    min
}
