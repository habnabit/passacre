use capnp::capability::Promise;
use capnp;

use super::error::PassacreResult;
use super::multibase::{Base, MultiBase};
use super::passacre_capnp::{derivation_parameters, deriver, schema, schema_utils, toplevel};
use super::passacre::{Algorithm, Kdf, PassacreGenerator};

pub struct StandardToplevel;

impl deriver::Server for StandardToplevel {
    fn derive(&mut self,
              params: deriver::DeriveParams,
              mut results: deriver::DeriveResults) -> Promise<(), capnp::Error> {
        let output = match derive(&params) {
            Ok(v) => v,
            Err(e) => return Promise::err(e.into()),
        };
        results.get().set_derived(&output);
        Promise::ok(())
    }
}

fn derive(params: &deriver::DeriveParams) -> PassacreResult<String> {
    let params = params.get()?;
    let site = params.get_site()?;
    let derivation = site.get_derivation()?;
    let input = params.get_user_input()?;
    let mut gen = generator_of_parameters(&derivation)?;
    let mb = multibase_of_schema(&site.get_schema()?)?;
    let mut nulls = derivation.get_increment();
    use super::passacre_capnp::derivation_parameters::kdf::Which::*;
    match derivation.get_kdf().which()? {
        Nulls(i) => nulls += i,
        Scrypt(s) => {
            let s = s?;
            gen.use_kdf(Kdf::Scrypt {
                n: s.get_n(),
                r: s.get_r(),
                p: s.get_p(),
            })?
        },
    };
    gen.absorb_username_password_site(
        input.get_username()?.as_bytes(),
        input.get_password()?.as_bytes(),
        input.get_sitename()?.as_bytes())?;
    gen.absorb_null_rounds(nulls as usize)?;
    Ok(mb.encode_from_generator(&mut gen)?)
}

fn generator_of_parameters(params: &derivation_parameters::Reader) -> PassacreResult<PassacreGenerator> {
    use super::passacre_capnp::derivation_parameters::Method::*;
    let alg = match params.get_method()? {
        Keccak => Algorithm::Keccak,
        Skein => Algorithm::Skein,
    };
    Ok(PassacreGenerator::new(alg)?)
}

impl schema_utils::Server for StandardToplevel {
    fn entropy_bits(&mut self,
                    params: schema_utils::EntropyBitsParams,
                    mut results: schema_utils::EntropyBitsResults) -> Promise<(), capnp::Error> {
        let mb = match multibase_of_schema(&pry!(pry!(params.get()).get_schema())) {
            Ok(v) => v,
            Err(e) => return Promise::err(e.into()),
        };
        results.get().set_bits(mb.entropy_bits() as u64);
        Promise::ok(())
    }
}

fn multibase_of_schema(schema: &schema::Reader) -> PassacreResult<MultiBase> {
    let mut ret = MultiBase::new();
    let mut loaded_words = false;
    for i in schema.get_value()?.iter() {
        use super::passacre_capnp::schema::base::value::Which::*;
        let b = match i.get_value().which()? {
            Characters(c) => {
                let cv = c?.iter().map(|r| r.map(Into::into)).collect::<Result<Vec<String>, _>>()?;
                Base::Characters(cv)
            },
            Words(()) => {
                if !loaded_words {
                    use super::passacre_capnp::word_list::source::Which::*;
                    match schema.get_words()?.get_source().which()? {
                        FilePath(s) => ret.load_words_from_path(::std::path::Path::new(s?))?,
                        _ => fail!(super::error::PassacreErrorKind::UserError),
                    }
                    loaded_words = true;
                }
                Base::Words
            },
            Separator(s) => Base::Separator(s?.into()),
            Subschema(s) => Base::NestedBase(multibase_of_schema(&s?)?),
        };
        for _ in 1..i.get_repeat() {
            ret.add_base(b.clone())?;
        }
        ret.add_base(b)?;
    }
    if schema.get_shuffle() {
        ret.enable_shuffle();
    }
    Ok(ret)
}

impl toplevel::Server for StandardToplevel {}
