pub mod diceware_en {
    pub const WORDS: &'static [&'static str] = &include!("diceware_en.list");
}

pub mod rfc2289 {
    pub const WORDS: &'static [&'static str] = &include!("rfc2289.list");
}

pub const WORDLISTS: &'static [(&'static str, &'static [&'static str])] = &[
    ("diceware_en", diceware_en::WORDS),
    ("rfc2289", rfc2289::WORDS),
];
