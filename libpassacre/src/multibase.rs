/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::io::BufRead;
use std::{fs, io, path, str};

use ramp::Int;

use error::PassacreErrorKind::*;
use error::PassacreResult;


fn int_of_bytes(bytes: &[u8]) -> Int {
    let mut ret = Int::zero();
    for b in bytes {
        ret = (ret << 8) + (*b as usize);
    }
    ret
}

fn length_one_string(c: char) -> String {
    let mut ret = String::with_capacity(c.len_utf8());
    ret.push(c);
    ret
}


pub enum Base {
    Separator(String),
    Characters(Vec<String>),
    Words,
}

impl Base {
    pub fn of_c_parts(which: ::libc::c_uint, string: &[u8]) -> PassacreResult<Base> {
        let result = match which {
            0 if !string.is_empty() => {
                match String::from_utf8(string.to_vec()) {
                    Ok(s) => Base::Separator(s),
                    _ => fail!(UserError),
                }
            },
            1 if !string.is_empty() => {
                match str::from_utf8(string) {
                    Ok(s) => Base::Characters(s.chars().map(length_one_string).collect()),
                    _ => fail!(UserError),
                }
            },
            2 if string.is_empty() => Base::Words,
            _ => fail!(UserError),
        };
        Ok(result)
    }
}

struct Words {
    words: Vec<String>,
    length: Int,
}

impl Words {
    fn new(words: Vec<String>) -> Words {
        let length = Int::from(words.len());
        Words {
            words: words,
            length: length,
        }
    }
}

pub struct MultiBase {
    bases: Vec<(Base, Int)>,
    words: Option<Words>,
    length_product: Int,
}

impl MultiBase {
    pub fn new() -> MultiBase {
        MultiBase {
            bases: Vec::new(),
            words: None,
            length_product: Int::one(),
        }
    }

    fn max_encodable_value(&self) -> Int {
        // XXX: https://github.com/Aatch/ramp/issues/23
        &self.length_product - &Int::one()
    }

    pub fn required_bytes(&self) -> usize {
        let mut ret = 0;
        let mut cur = self.max_encodable_value();
        while cur > 0 {
            ret += 1;
            cur = cur >> 8;
        }
        ret
    }

    pub fn add_base(&mut self, base: Base) -> PassacreResult<()> {
        let length = match &base {
            &Base::Separator(_) => Int::one(),
            &Base::Characters(ref s) => Int::from(s.len()),
            &Base::Words => {
                match &self.words {
                    &Some(ref w) => w.length.clone(),
                    &None => fail!(UserError),
                }
            },
        };
        self.length_product = &self.length_product * &length;
        self.bases.push((base, length));
        Ok(())
    }

    pub fn set_words(&mut self, words: Vec<String>) -> PassacreResult<()> {
        if self.words.is_some() {
            fail!(UserError);
        }
        self.words = Some(Words::new(words));
        Ok(())
    }

    pub fn load_words_from_path(&mut self, path: &path::Path) -> PassacreResult<()> {
        // XXX: real error handling
        let infile = fs::File::open(path).unwrap();
        let lines = io::BufReader::new(infile).lines().collect::<io::Result<Vec<String>>>().unwrap();
        self.set_words(lines)
    }

    fn encode(&self, mut n: Int) -> PassacreResult<String> {
        if n < 0 || n >= self.length_product {
            fail!(DomainError);
        }
        let mut ret = Vec::new();
        for &(ref base, ref length) in self.bases.iter().rev() {
            if let &Base::Separator(ref s) = base {
                ret.push(s.as_str());
            } else {
                let (next_n, d) = n.divmod(length);
                let d = usize::from(&d);
                match base {
                    &Base::Characters(ref cs) => ret.push(cs[d].as_str()),
                    &Base::Words => {
                        match &self.words {
                            &Some(ref w) => ret.push(w.words[d].as_str()),
                            &None => fail!(UserError),
                        }
                    },
                    _ => unreachable!(),
                }
                n = next_n;
            }
        }
        ret.reverse();
        Ok(ret.concat())
    }

    pub fn encode_from_bytes(&self, bytes: &[u8]) -> PassacreResult<String> {
        self.encode(int_of_bytes(bytes))
    }
}


#[cfg(test)]
mod tests {
    use ramp::Int;

    use error::PassacreErrorKind::*;
    use super::{Base, MultiBase, length_one_string};

    macro_rules! multibase_tests {
        ($constructor:ident,
         $max_value:expr,
         $req_bytes:expr,
         [ $( $decoded:expr => $encoded:expr ),* ],
         [ $( $encoding_failure:expr ),* ]
         ) => {

            fnconcat!{#[test] [test_, $constructor, _max_encodable_value]() {
                let b = $constructor();
                let max_value = Int::from($max_value);
                assert_eq!(b.max_encodable_value(), max_value);
            }}

            fnconcat!{#[test] [test_, $constructor, _required_bytes]() {
                let b = $constructor();
                assert_eq!(b.required_bytes(), $req_bytes);
            }}

            parametrize_test!{[test_, $constructor, _encoding], [
                (decoded: u64, encoded: &'static str),
                $(
                    ($decoded, $encoded),
                )*
            ], {
                let b = $constructor();
                let v = Int::from(decoded);
                assert_eq!(b.encode(v).unwrap(), encoded);
            }}

            parametrize_test!{[test_, $constructor, _encoding_failure], [
                (value: u64),
                $(
                    ($encoding_failure),
                )*
            ], {
                let b = $constructor();
                let v = Int::from(value);
                assert_eq!(b.encode(v).unwrap_err().kind, DomainError);
            }}

        }
    }

    const DIGITS: &'static str = "0123456789";
    const HEXDIGITS: &'static str = "0123456789abcdef";

    fn characters(cs: &'static str) -> Base {
        Base::Characters(cs.chars().map(length_one_string).collect())
    }

    fn base_2x10() -> MultiBase {
        let mut b = MultiBase::new();
        b.add_base(characters(DIGITS)).unwrap();
        b.add_base(characters(DIGITS)).unwrap();
        b
    }

    multibase_tests!(
        base_2x10,
        99,
        1,
        [5 => "05",
         9 => "09",
         36 => "36",
         94 => "94"],
        [100, 105]);

    fn base_2x16() -> MultiBase {
        let mut b = MultiBase::new();
        b.add_base(characters(HEXDIGITS)).unwrap();
        b.add_base(characters(HEXDIGITS)).unwrap();
        b
    }

    multibase_tests!(
        base_2x16,
        0xff,
        1,
        [0x5 => "05",
         0xc => "0c",
         0x36 => "36",
         0xfe => "fe"],
        [0x100, 0x105]);

    fn base_4_3_2() -> MultiBase {
        let mut b = MultiBase::new();
        b.add_base(characters("abcd")).unwrap();
        b.add_base(characters("abc")).unwrap();
        b.add_base(characters("ab")).unwrap();
        b
    }

    multibase_tests!(
        base_4_3_2,
        23,  // 4 * 3 * 2 == 24
        1,
        [0 => "aaa",
         5 => "acb",
         9 => "bbb",
         11 => "bcb",
         17 => "ccb",
         23 => "dcb"],
        [24]);
}
