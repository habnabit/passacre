#ifndef _PASSACRE_H_
#define _PASSACRE_H_ 1

#include <stddef.h>
#include "passacre_export.h"


enum passacre_gen_algorithm {
    PASSACRE_KECCAK,
    PASSACRE_SKEIN,
};

struct passacre_gen_state;

PASSACRE_EXPORT size_t passacre_gen_size(void);
PASSACRE_EXPORT int passacre_gen_init(struct passacre_gen_state *, enum passacre_gen_algorithm);
PASSACRE_EXPORT int passacre_gen_absorb(struct passacre_gen_state *, unsigned char *, size_t);
PASSACRE_EXPORT int passacre_gen_absorb_null_rounds(struct passacre_gen_state *, size_t);
PASSACRE_EXPORT int passacre_gen_squeeze(struct passacre_gen_state *, unsigned char *, size_t);

#endif
