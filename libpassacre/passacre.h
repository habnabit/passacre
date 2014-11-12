/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
 * SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
 * OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
 * CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

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
