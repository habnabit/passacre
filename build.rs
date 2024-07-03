fn main() {
    cc::Build::new()
        .file("src/keccak/KeccakF-1600-opt64.c")
        .file("src/keccak/KeccakSponge.c")
        .file("src/skein/skein.c")
        .file("src/skein/skeinBlockNo3F.c")
        .file("src/skein/threefish256Block.c")
        .file("src/skein/threefish512Block.c")
        .file("src/skein/threefish1024Block.c")
        .file("src/skein/skeinApi.c")
        .file("src/skein/threefishApi.c")
        .file("src/scrypt/sha256.c")
        .file("src/scrypt/crypto_scrypt-nosse.c")
        // .define("HAVE_SYS_ENDIAN_H", "1")
        // .define("HAVE_DECL_BE64ENC", "1")
        .define("HAVE_ALIGNED_ALLOC", "1")
        // .define("HAVE_POSIX_MEMALIGN", "1")
        .compile("passacre_deps")
    // ${KECCAKF}
    // scrypt/crypto_scrypt-${SCRYPTVER}.c
}
