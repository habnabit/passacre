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

struct WordList {
  source :union {
    none @0 :Void;
    named @1 :Text;
    filePath @2 :Text;
    words @3 :List(Text);
  }
}

struct Schema {
  name @0 :Text;
  value @1 :List(Base);
  words @2 :WordList;
  shuffle @3 :Bool;

  struct Base {
    value :union {
      characters @0 :List(Text);
      words @1 :Void;
      separator @2 :Text;
      subschema @3 :Schema;
    }
    repeat @4 :UInt32 = 1;
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