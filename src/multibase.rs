/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::borrow::Cow;
use std::collections::BTreeMap;
use std::io::BufRead;
use std::{fs, io, path, str};

use num_bigint::BigInt as Int;
use num_traits::{Euclid, One, ToPrimitive, Zero};

use crate::error::{PassacreError, PassacreError::*, PassacreResult};
use crate::passacre::PassacreGenerator;

fn borrow_string(s: &String) -> Cow<str> {
    return Cow::Borrowed(s.as_str());
}

fn int_of_bytes(bytes: &[u8]) -> Int {
    let mut ret = Int::zero();
    for b in bytes {
        ret = (ret << 8) + (*b as usize);
    }
    ret
}

fn factorial(n: usize) -> Int {
    if n < 2 {
        return Int::one();
    }
    (2..n).fold(Int::from(n), |acc, i| acc * Int::from(i))
}

fn length_one_string(c: char) -> String {
    let mut ret = String::with_capacity(c.len_utf8());
    ret.push(c);
    ret
}

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum Base {
    Separator(String),
    Characters(Vec<String>),
    Words,
    NestedBase(MultiBase),
}

impl Base {
    pub fn of_c_parts(which: ::libc::c_uint, string: &[u8]) -> PassacreResult<Base> {
        let result = match which {
            0 if !string.is_empty() => match String::from_utf8(string.to_vec()) {
                Ok(s) => Base::Separator(s),
                _ => fail!(UserError),
            },
            1 if !string.is_empty() => match str::from_utf8(string) {
                Ok(s) => Base::Characters(s.chars().map(length_one_string).collect()),
                _ => fail!(UserError),
            },
            2 if string.is_empty() => Base::Words,
            _ => fail!(UserError),
        };
        Ok(result)
    }
}

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord)]
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

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord)]
struct BaseInfo {
    length: Int,
    positions: Vec<usize>,
}

impl BaseInfo {
    fn new(length: Int) -> BaseInfo {
        BaseInfo {
            length: length,
            positions: Vec::new(),
        }
    }
}

#[derive(Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct MultiBase {
    bases: BTreeMap<Base, BaseInfo>,
    n_bases: usize,
    words: Option<Words>,
    length_product: Int,
    shuffle: bool,
}

impl MultiBase {
    pub fn new() -> MultiBase {
        MultiBase {
            bases: BTreeMap::new(),
            n_bases: 0,
            words: None,
            length_product: Int::one(),
            shuffle: false,
        }
    }

    fn max_encodable_value(&self) -> Int {
        &self.length_product - 1
    }

    pub fn required_bytes(&self) -> usize {
        ((self.max_encodable_value().bits() + 7) / 8) as usize
    }

    pub fn entropy_bits(&self) -> usize {
        self.length_product.bits() as usize
    }

    pub fn enable_shuffle(&mut self) {
        if self.shuffle {
            return;
        }
        self.length_product = self.bases.values().fold(
            &self.length_product * factorial(self.n_bases),
            |acc, info| acc / factorial(info.positions.len()),
        );
        self.shuffle = true;
    }

    pub fn add_base(&mut self, base: Base) -> PassacreResult<()> {
        if self.shuffle {
            fail!(UserError);
        }
        let length = match &base {
            &Base::Separator(_) => Int::one(),
            &Base::Characters(ref s) => Int::from(s.len()),
            &Base::Words => match &self.words {
                &Some(ref w) => w.length.clone(),
                &None => fail!(UserError),
            },
            &Base::NestedBase(ref b) => b.length_product.clone(),
        };
        self.length_product = &self.length_product * &length;
        let entry = self
            .bases
            .entry(base)
            .or_insert_with(move || BaseInfo::new(length));
        entry.positions.push(self.n_bases);
        self.n_bases = self.n_bases + 1;
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
        let infile = fs::File::open(path)?;
        let lines = io::BufReader::new(infile)
            .lines()
            .collect::<io::Result<Vec<String>>>()?;
        self.set_words(lines)
    }

    fn bases_ref_vec(&self) -> Vec<(&Base, &Int, usize)> {
        let mut ret = vec![None; self.n_bases];
        for (e, (base, info)) in self.bases.iter().enumerate() {
            for &i in info.positions.iter() {
                ret[i] = Some((base, &info.length, e));
            }
        }
        // safety: n_bases should be calculated such that this will fill every slot
        ret.into_iter().collect::<Option<Vec<_>>>().unwrap()
    }

    fn encode(&self, mut n: Int) -> PassacreResult<String> {
        if n < Int::zero() || n >= self.length_product {
            fail!(DomainError);
        }
        let bases = self.bases_ref_vec();
        let mut ret: Vec<Cow<str>> = Vec::with_capacity(self.n_bases);
        for &(base, length, _) in bases.iter().rev() {
            if let &Base::Separator(ref s) = base {
                ret.push(borrow_string(s));
                continue;
            }
            let (next_n, d) = n.div_rem_euclid(length);
            ret.push(match base {
                // safety: d is the remainder of length, which should've been a usize coming in
                &Base::Characters(ref cs) => borrow_string(&cs[d.to_usize().unwrap()]),
                &Base::Words => match &self.words {
                    // safety: d is the remainder of length, which should've been a usize coming in
                    &Some(ref w) => borrow_string(&w.words[d.to_usize().unwrap()]),
                    &None => fail!(UserError),
                },
                &Base::NestedBase(ref b) => Cow::Owned(b.encode(d)?),
                _ => unreachable!(),
            });
            n = next_n;
        }
        if self.shuffle {
            unimplemented!();
        } else {
            ret.reverse();
        }
        Ok(ret.concat())
    }

    pub fn encode_from_bytes(&self, bytes: &[u8]) -> PassacreResult<String> {
        self.encode(int_of_bytes(bytes))
    }

    pub fn encode_from_generator(&self, gen: &mut PassacreGenerator) -> PassacreResult<String> {
        let mut buf = vec![0u8; self.required_bytes()];
        loop {
            gen.squeeze(&mut buf)?;
            match self.encode(int_of_bytes(&buf)) {
                Err(PassacreError::DomainError) => continue,
                x => return x,
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::{length_one_string, Base, MultiBase};
    use crate::error::PassacreError::*;
    use parameterized::parameterized;

    #[test]
    fn test_no_words_base_without_words() {
        let mut b = MultiBase::new();
        assert!(matches!(b.add_base(Base::Words).unwrap_err(), UserError));
    }

    macro_rules! multibase_tests {
        ($constructor:ident,
         $max_value:expr,
         $req_bytes:expr,
         [ $( $decoded:expr => $encoded:expr ),* ],
         [ $( $encoding_failure:expr ),* ]
         { $( $i:item )* }
         ) => {

            mod $constructor {
                use super::*;
                use crate::multibase::PassacreResult;
                use num_bigint::BigInt as Int;
                use num_traits::ToPrimitive;

                #[test]
                fn test_max_encodable_value() -> PassacreResult<()> {
                    let b = make_mb()?;
                    let max_value = Int::from($max_value);
                    assert_eq!(b.max_encodable_value(), max_value);
                    Ok(())
                }

                #[test]
                fn test_required_bytes() -> PassacreResult<()> {
                    let b = make_mb()?;
                    assert_eq!(b.required_bytes(), $req_bytes);
                    Ok(())
                }

                #[test]
                fn test_all_unique() -> PassacreResult<()> {
                    let b = make_mb()?;
                    let l: usize = b.length_product.to_usize().unwrap();
                    let mut h = HashMap::with_capacity(l);
                    for i in 0..l {
                        h.entry(b.encode(Int::from(i))?).or_insert_with(|| vec![]).push(i);
                    }
                    let dupes: Vec<_> = h.into_iter()
                        .filter(|&(_, ref c)| c.len() > 1)
                        .collect();
                    assert_eq!(dupes, vec![]);
                    Ok(())
                }

                #[parameterized(
                    decoded = { $( $decoded, )* },
                    encoded = { $( $encoded, )* },
                )]
                fn test_encoding(decoded: u64, encoded: &'static str) -> PassacreResult<()> {
                    let b = make_mb()?;
                    let v = Int::from(decoded);
                    assert_eq!(b.encode(v)?, encoded);
                    Ok(())
                }


                #[parameterized(
                    value = { $( $encoding_failure, )* },
                )]
                fn test_encoding_failure(value: u64) -> PassacreResult<()> {
                    let b = make_mb()?;
                    let v = Int::from(value);
                    assert!(matches!(b.encode(v).unwrap_err(), DomainError));
                    Ok(())
                }

                $( $i )*
            }
        }
    }

    const DIGITS: &'static str = "0123456789";
    const HEXDIGITS: &'static str = "0123456789abcdef";

    fn characters(cs: &'static str) -> Base {
        Base::Characters(cs.chars().map(length_one_string).collect())
    }

    multibase_tests!(
        base_2x10,
        99,
        1,
        [5 => "05",
         9 => "09",
         36 => "36",
         94 => "94"],
        [100, 105]
    {
        fn make_mb() -> PassacreResult<MultiBase> {
            let mut b = MultiBase::new();
            b.add_base(characters(DIGITS))?;
            b.add_base(characters(DIGITS))?;
            Ok(b)
        }
    });

    multibase_tests!(
        base_2x16,
        0xff,
        1,
        [0x5 => "05",
         0xc => "0c",
         0x36 => "36",
         0xfe => "fe"],
        [0x100, 0x105]
    {
        fn make_mb() -> PassacreResult<MultiBase> {
            let mut b = MultiBase::new();
            b.add_base(characters(HEXDIGITS))?;
            b.add_base(characters(HEXDIGITS))?;
            Ok(b)
        }
    });

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
        [24]
    {
        fn make_mb() -> PassacreResult<MultiBase> {
            let mut b = MultiBase::new();
            b.add_base(characters("abcd"))?;
            b.add_base(characters("abc"))?;
            b.add_base(characters("ab"))?;
            Ok(b)
        }
    });

    // fn base_4_3_2_shuffled() -> MultiBase {
    //     let mut b = MultiBase::new();
    //     b.add_base(characters("abcd"))?;
    //     b.add_base(characters("efg"))?;
    //     b.add_base(characters("hi"))?;
    //     b.enable_shuffle();
    //     b
    // }

    // multibase_tests!(
    //     base_4_3_2_shuffled,
    //     143,  // 4 * 3 * 2 * 6 == 144
    //     1,
    //     [0 => "hea",
    //      23 => "igd",
    //      37 => "xxx",
    //      61 => "xxx"],
    //     [144]);

    multibase_tests!(
        base_2x3_words,
        8,  // 3 * 3 == 9
        1,
        [0 => "spam spam",
         3 => "eggs spam",
         8 => "sausage sausage"],
        [9, 12, 24]
    {
        fn make_mb() -> PassacreResult<MultiBase> {
            let mut b = MultiBase::new();
            let words = ["spam", "eggs", "sausage"].into_iter().map(|s| s.into()).collect();
            b.set_words(words)?;
            b.add_base(Base::Words)?;
            b.add_base(Base::Separator(String::from(" ")))?;
            b.add_base(Base::Words)?;
            Ok(b)
        }
    });

    multibase_tests!(
        base_2x3_words_and_2x10,
        899,  // 3 * 3 * 10 * 10 == 900
        2,
        [0 => "spam0 0spam",
         3 => "spam0 1spam",
         8 => "spam0 2sausage",
         29 => "spam0 9sausage",
         30 => "spam1 0spam",
         99 => "spam3 3spam",
         100 => "spam3 3eggs",
         299 => "spam9 9sausage",
         300 => "eggs0 0spam",
         899 => "sausage9 9sausage"],
        [900, 1000]
    {
        fn make_mb() -> PassacreResult<MultiBase> {
            let mut b = MultiBase::new();
            let words = ["spam", "eggs", "sausage"].into_iter().map(|s| s.into()).collect();
            b.set_words(words)?;
            b.add_base(Base::Words)?;
            b.add_base(characters(DIGITS))?;
            b.add_base(Base::Separator(String::from(" ")))?;
            b.add_base(characters(DIGITS))?;
            b.add_base(Base::Words)?;
            Ok(b)
        }
    });
}
