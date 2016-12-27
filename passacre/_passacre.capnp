@0xe9a7c140af85957a;

struct DerivationParameters {
  method @0 :Method;
  kdf :union {
    nulls @1 :Int64;
    scrypt @2 :Scrypt;
  }
  increment @3 :Int64;

  enum Method {
    keccak @0;
    skein @1;
  }
}

struct Scrypt {
  n @0 :UInt64;
  r @1 :UInt32;
  p @2 :UInt32;
}

struct Schema {
  value @0 :List(Base);
  shuffle @1 :Bool;

  struct Base {
    union {
      choices @0 :List(Text);
      wordFile @1 :Text;
      wellKnown @2 :Text;
      separator @3 :Text;
      subschema @4 :Schema;
      sameAs @5 :UInt32;
    }
  }
}

interface SchemaUtils {
  entropyBits @0 (schema :Schema) -> (bits :UInt64);
}

struct SiteConfiguration {
  derivation @0 :DerivationParameters;
  schema @1 :Schema;
  inherits @2 :List(Text);
  yubikey :union {
    noYubikey @3 :Void;
    yubikeySlot @4 :UInt8;
  }
}

struct GlobalConfiguration {
  siteDefaults @0 :SiteConfiguration;
  alwaysConfirmPasswords @1 :Bool;
  siteNameHashing @2 :SiteNameHashingConfiguration;

  struct SiteNameHashingConfiguration {
    enabled @0 :Bool;
    derivation @1 :DerivationParameters;
    tolerance @2 :Int64;
  }
}

struct UserInput {
  username @0 :Text;
  password @1 :Text;
  sitename @2 :Text;
}

interface Deriver {
  derive @0 (site: SiteConfiguration, userInput :UserInput)
         -> (derived: Text);
}

interface Toplevel extends (SchemaUtils, Deriver) {}
