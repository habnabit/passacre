use std::path::PathBuf;

use pyo3::prelude::*;

use crate::error::PassacreResult;
use crate::multibase::{Base, MultiBase};
use crate::passacre::{Algorithm, Kdf, PassacreGenerator};

fn multibase_of_schema(schema: &Bound<'_, PyAny>) -> PassacreResult<MultiBase> {
    let mut ret = MultiBase::new();
    let mut loaded_words = false;
    for item_res in schema.get_item("value")?.iter()? {
        let item = item_res?;
        let (key, item_value) = item
            .get_item("value")?
            .call_method0("copy")?
            .call_method0("popitem")?
            .extract::<(String, Bound<'_, PyAny>)>()?;
        let base = match key.as_str() {
            "characters" => Base::Characters(item_value.extract()?),
            "separator" => Base::Separator(item_value.extract()?),
            "subschema" => Base::NestedBase(multibase_of_schema(&item_value)?),
            "words" => {
                if !loaded_words {
                    let (key, item_value) = schema
                        .get_item("words")?
                        .get_item("source")?
                        .call_method0("copy")?
                        .call_method0("popitem")?
                        .extract::<(String, Bound<'_, PyAny>)>()?;
                    if key != "filePath" {
                        panic!("only file path loading");
                    }
                    let path = item_value.extract::<PathBuf>()?;
                    ret.load_words_from_path(&path)?;
                    loaded_words = true;
                }
                Base::Words
            }
            s => panic!("oh no what?? {s:#?}"),
        };
        let repeat = item
            .call_method1("get", ("repeat", 1))?
            .extract::<usize>()?;
        for _ in 1..repeat {
            ret.add_base(base.clone())?;
        }
        ret.add_base(base)?;
    }

    if schema.call_method1("get", ("shuffle",))?.is_truthy()? {
        ret.enable_shuffle();
    }
    Ok(ret)
}

///
#[pyfunction]
fn derive(
    derivation_method: &str,
    derivation_kdf: &Bound<'_, PyAny>,
    derivation_increment: usize,
    schema: &Bound<'_, PyAny>,
    username: &str,
    password: &str,
    sitename: &str,
) -> PassacreResult<String> {
    let mut generator = {
        let method = match derivation_method {
            "keccak" => Algorithm::Keccak,
            "skein" => Algorithm::Skein,
            _ => panic!("oh no"),
        };
        PassacreGenerator::new(method)?
    };
    let mb = multibase_of_schema(schema)?;

    let mut nulls = derivation_increment;
    if derivation_kdf.is_truthy()? {
        let (key, item_value) = derivation_kdf
            .call_method0("copy")?
            .call_method0("popitem")?
            .extract::<(String, Bound<'_, PyAny>)>()?;
        match key.as_str() {
            "nulls" => {
                nulls += item_value.extract::<usize>()?;
            }
            "scrypt" => {
                generator.use_kdf(Kdf::Scrypt {
                    n: item_value.get_item("n")?.extract()?,
                    r: item_value.get_item("r")?.extract()?,
                    p: item_value.get_item("p")?.extract()?,
                })?;
            }
            _ => {}
        }
    }

    generator.absorb_username_password_site(
        username.as_bytes(),
        password.as_bytes(),
        sitename.as_bytes(),
    )?;
    generator.absorb_null_rounds(nulls)?;
    Ok(mb.encode_from_generator(&mut generator)?)
}

#[pyfunction]
fn entropy_bits(schema: &Bound<'_, PyAny>) -> PassacreResult<usize> {
    let mb = multibase_of_schema(schema)?;
    Ok(mb.entropy_bits())
}

///
#[pymodule]
fn _pyo3_backend(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add(
        "PassacreException",
        m.py().get_type_bound::<crate::error::PassacreException>(),
    )?;
    m.add_function(wrap_pyfunction!(derive, m)?)?;
    m.add_function(wrap_pyfunction!(entropy_bits, m)?)?;
    Ok(())
}
