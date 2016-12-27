/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

use std::borrow::Cow;
use std::collections::BTreeMap;
use std::str;

use ramp::Int;

use error::PassacreErrorKind::*;
use error::{PassacreError, PassacreResult};
use passacre::PassacreGenerator;


fn borrow_string(s: &String) -> Cow<str> {
    return Cow::Borrowed(s.as_str())
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
    (2..n).fold(
        Int::from(n),
        |acc, i| acc * Int::from(i))
}


#[derive(Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum Base {
    Separator(String),
    Choices(Vec<String>),
    NestedBase(MultiBase),
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
    length_product: Int,
    shuffle: bool,
}

impl MultiBase {
    pub fn new() -> MultiBase {
        MultiBase {
            bases: BTreeMap::new(),
            n_bases: 0,
            length_product: Int::one(),
            shuffle: false,
        }
    }

    fn max_encodable_value(&self) -> Int {
        &self.length_product - 1
    }

    pub fn required_bytes(&self) -> usize {
        ((self.max_encodable_value().bit_length() + 7) / 8) as usize
    }

    pub fn entropy_bits(&self) -> usize {
        self.length_product.bit_length() as usize
    }

    pub fn enable_shuffle(&mut self) {
        if self.shuffle {
            return;
        }
        self.length_product = self.bases
            .values()
            .fold(
                &self.length_product * factorial(self.n_bases),
                |acc, info| acc / factorial(info.positions.len()));
        self.shuffle = true;
    }

    pub fn add_base(&mut self, base: Base) -> PassacreResult<()> {
        if self.shuffle {
            fail!(UserError);
        }
        let length = match &base {
            &Base::Separator(_) => Int::one(),
            &Base::Choices(ref s) => Int::from(s.len()),
            &Base::NestedBase(ref b) => b.length_product.clone(),
        };
        self.length_product = &self.length_product * &length;
        let mut entry = self.bases.entry(base).or_insert_with(move || BaseInfo::new(length));
        entry.positions.push(self.n_bases);
        self.n_bases = self.n_bases + 1;
        Ok(())
    }

    pub fn repeat_base(&mut self, index: usize) -> PassacreResult<()> {
        if self.shuffle {
            fail!(UserError);
        }
        let n_bases = self.n_bases;
        let length = {
            let info = self.bases.values_mut()
                .find(|info| info.positions.contains(&index))
                .ok_or(UserError)?;
            info.positions.push(n_bases);
            info.length.clone()
        };
        self.length_product = &self.length_product * &length;
        self.n_bases = self.n_bases + 1;
        Ok(())
    }

    fn unshuffled_bases_ref_vec(&self) -> Vec<(&Base, &Int, usize)> {
        let mut ret = vec![None; self.n_bases];
        for (e, (base, info)) in self.bases.iter().enumerate() {
            for &i in info.positions.iter() {
                ret[i] = Some((base, &info.length, e));
            }
        }
        ret.into_iter().collect::<Option<Vec<_>>>().unwrap()
    }

    fn bases_ref_vec(&self, n: &mut Int) -> Vec<(&Base, &Int, usize)> {
        let bases = self.unshuffled_bases_ref_vec();
        if !self.shuffle {
            return bases;
        }
        let mut bases_by_count: Vec<(usize, &BaseInfo)> = self.bases
            .iter()
            .map(|(_, info)| (info.positions.len(), info))
            .collect();
        bases_by_count.sort();
        let (_, last_base) = bases_by_count.pop().unwrap();
        let mut ret = vec![None; self.n_bases];
        for (_, info) in bases_by_count.into_iter() {
            let mut choices: Vec<usize> = ret.iter()
                .enumerate()
                .filter_map(|t| match t {
                    (e, &None) => Some(e),
                    _ => None,
                })
                .collect();
            for &src_position in &info.positions {
                let (next_n, choice) = n.divmod(&Int::from(choices.len()));
                let dst_position = choices.swap_remove(usize::from(&choice));
                ret[dst_position] = Some(bases[src_position]);
                *n = next_n;
            }
        }
        for (dst, &src) in ret.iter_mut().filter(|o| o.is_none()).zip(&last_base.positions) {
            *dst = Some(bases[src]);
        }
        ret.into_iter().collect::<Option<Vec<_>>>().unwrap()
    }

    fn encode(&self, mut n: Int) -> PassacreResult<String> {
        if n < 0 || n >= self.length_product {
            fail!(DomainError);
        }
        let bases = self.bases_ref_vec(&mut n);
        let mut ret: Vec<Cow<str>> = Vec::with_capacity(self.n_bases);
        for &(base, length, _) in bases.iter().rev() {
            if let &Base::Separator(ref s) = base {
                ret.push(borrow_string(s));
                continue;
            }
            let (next_n, d) = n.divmod(length);
            ret.push(match base {
                &Base::Choices(ref cs) => borrow_string(&cs[usize::from(&d)]),
                &Base::NestedBase(ref b) => Cow::Owned(try!(b.encode(d))),
                _ => unreachable!(),
            });
            n = next_n;
        }
        ret.reverse();
        Ok(ret.concat())
    }

    pub fn encode_from_bytes(&self, bytes: &[u8]) -> PassacreResult<String> {
        self.encode(int_of_bytes(bytes))
    }

    pub fn encode_from_generator(&self, gen: &mut PassacreGenerator) -> PassacreResult<String> {
        let mut buf = vec![0u8; self.required_bytes()];
        loop {
            try!(gen.squeeze(&mut buf));
            match self.encode(int_of_bytes(&buf)) {
                Err(PassacreError { kind: DomainError, .. }) => continue,
                x => return x,
            }
        }
    }
}


#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use ramp::Int;

    use error::PassacreErrorKind::*;
    use super::{Base, MultiBase};

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

            fnconcat!{#[test] [test_, $constructor, _all_unique]() {
                let b = $constructor();
                let l: usize = ::std::convert::From::from(&b.length_product);
                let mut h = HashMap::with_capacity(l);
                for i in 0..l {
                    h.entry(b.encode(Int::from(i)).unwrap()).or_insert_with(|| vec![]).push(i);
                }
                let dupes: Vec<_> = h.into_iter()
                    .filter(|&(_, ref c)| c.len() > 1)
                    .collect();
                assert_eq!(dupes, vec![]);
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

    fn length_one_string(c: char) -> String {
        let mut ret = String::with_capacity(c.len_utf8());
        ret.push(c);
        ret
    }

    fn characters(cs: &'static str) -> Base {
        Base::Choices(cs.chars().map(length_one_string).collect())
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

    fn base_4_3_2_shuffled() -> MultiBase {
        let mut b = MultiBase::new();
        b.add_base(characters("abcd")).unwrap();
        b.add_base(characters("efg")).unwrap();
        b.add_base(characters("hi")).unwrap();
        b.enable_shuffle();
        b
    }

    multibase_tests!(
        base_4_3_2_shuffled,
        143,  // 4 * 3 * 2 * 6 == 144
        1,
        [0 => "hea",
         23 => "afi",
         37 => "eic",
         61 => "fhc",
         143 => "dgi"],
        [144]);

    fn base_2x3_words() -> MultiBase {
        let mut b = MultiBase::new();
        let words = ["spam", "eggs", "sausage"].into_iter().map(|&s| s.into()).collect();
        b.add_base(Base::Choices(words)).unwrap();
        b.add_base(Base::Separator(String::from(" "))).unwrap();
        b.repeat_base(0).unwrap();
        b
    }

    multibase_tests!(
        base_2x3_words,
        8,  // 3 * 3 == 9
        1,
        [0 => "spam spam",
         3 => "eggs spam",
         8 => "sausage sausage"],
        [9, 12, 24]);

    fn base_2x3_words_and_2x10() -> MultiBase {
        let mut b = MultiBase::new();
        let words = ["spam", "eggs", "sausage"].into_iter().map(|&s| s.into()).collect();
        b.add_base(Base::Choices(words)).unwrap();
        b.add_base(characters(DIGITS)).unwrap();
        b.add_base(Base::Separator(String::from(" "))).unwrap();
        b.add_base(characters(DIGITS)).unwrap();
        b.repeat_base(0).unwrap();
        b
    }

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
        [900, 1000]);

    fn base_1x5_and_3x5_shuffled() -> MultiBase {
        let mut b = MultiBase::new();
        for _ in 0..3 {
            b.add_base(characters("02468")).unwrap();
        }
        b.add_base(characters("13579")).unwrap();
        b.enable_shuffle();
        b
    }

    multibase_tests!(
        base_1x5_and_3x5_shuffled,
        2499,  // 4 * 5 ** 4 == 2500
        2,
        [0 => "1000",
         1 => "0100",
         2 => "0010",
         3 => "0001",
         4 => "1002",
         2499 => "8889"],
        [2500, 12500, 31250]);
}
