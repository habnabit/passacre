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
#include <stdint.h>


enum passacre_gen_algorithm {
    PASSACRE_KECCAK = 0,
    PASSACRE_SKEIN = 1,
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
int passacre_gen_finished(struct passacre_gen_state *);
size_t passacre_error(int, unsigned char *, size_t);

#endif
