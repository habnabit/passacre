macro_rules! wordlists {
    ($($name:ident ,)*) => {
        $( pub mod $name {
            pub const WORDS: &'static [&'static str] = &include!(concat!(stringify!($name), ".list"));
        } )*

        pub const WORDLISTS: &'static [(&'static str, &'static [&'static str])] = &[ $(
            (stringify!($name), $name::WORDS),
        )* ];
    };
}

wordlists! {
    diceware_en,
    pgp_even, pgp_odd,
    rfc2289,
}
