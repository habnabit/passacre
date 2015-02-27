import cffi


ffi = cffi.FFI()
ffi.cdef("""

enum passacre_gen_algorithm {
    PASSACRE_KECCAK,
    PASSACRE_SKEIN,
    ...
};

struct passacre_gen_state;

size_t passacre_gen_size(void);
int passacre_gen_init(struct passacre_gen_state *, enum passacre_gen_algorithm);
int passacre_gen_absorb_username_password_site(struct passacre_gen_state *, const unsigned char *, size_t, const unsigned char *, size_t, const unsigned char *, size_t);
int passacre_gen_absorb_null_rounds(struct passacre_gen_state *, size_t);
int passacre_gen_squeeze(struct passacre_gen_state *, unsigned char *, size_t);

""")

preamble = '#include "passacre.h"'
