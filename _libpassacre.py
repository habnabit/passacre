import cffi


ffi = cffi.FFI()
ffi.cdef("""

typedef unsigned char *(*passacre_allocator)(size_t, const void *);


enum passacre_mb_base {
    PASSACRE_SEPARATOR,
    PASSACRE_CHARACTERS,
    PASSACRE_WORDS,
    ...
};

struct passacre_mb_state;

size_t passacre_mb_size(void);
size_t passacre_mb_align(void);
int passacre_mb_init(struct passacre_mb_state *);
int passacre_mb_required_bytes(struct passacre_mb_state *, size_t *);
int passacre_mb_add_base(
    struct passacre_mb_state *, enum passacre_mb_base,
    const unsigned char *, size_t);
int passacre_mb_load_words_from_path(
    struct passacre_mb_state *, const unsigned char *, size_t);
int passacre_mb_encode_from_bytes(
    struct passacre_mb_state *,
    const unsigned char *, size_t, passacre_allocator, const void *);
int passacre_mb_finished(struct passacre_mb_state *);


enum passacre_gen_algorithm {
    PASSACRE_KECCAK,
    PASSACRE_SKEIN,
    ...
};

struct passacre_gen_state;

size_t passacre_gen_size(void);
size_t passacre_gen_align(void);
size_t passacre_gen_scrypt_buffer_size(void);
int passacre_gen_init(
    struct passacre_gen_state *, enum passacre_gen_algorithm);
int passacre_gen_use_scrypt(
    struct passacre_gen_state *,
    uint64_t, uint32_t, uint32_t, unsigned char *);
int passacre_gen_absorb_username_password_site(
    struct passacre_gen_state *, const unsigned char *, size_t,
    const unsigned char *, size_t, const unsigned char *, size_t);
int passacre_gen_absorb_null_rounds(struct passacre_gen_state *, size_t);
int passacre_gen_squeeze(struct passacre_gen_state *, unsigned char *, size_t);
int passacre_gen_squeeze_password(
    struct passacre_gen_state *, struct passacre_mb_state *,
    passacre_allocator, const void *);
int passacre_gen_finished(struct passacre_gen_state *);


size_t passacre_error(int, unsigned char *, size_t);

""")

preamble = '#include "passacre.h"'
