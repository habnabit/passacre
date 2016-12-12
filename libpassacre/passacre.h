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


typedef unsigned char *(*passacre_allocator)(size_t, const void *);

enum passacre_error_type {
    PASSACRE_PANIC_ERROR = -1,
    PASSACRE_KECCAK_ERROR = -2,
    PASSACRE_SKEIN_ERROR = -3,
    PASSACRE_SCRYPT_ERROR = -4,
    PASSACRE_USER_ERROR = -5,
    PASSACRE_INTERNAL_ERROR = -6,
    PASSACRE_DOMAIN_ERROR = -7,
    PASSACRE_ALLOCATOR_ERROR = -8,
};


enum passacre_mb_base {
    PASSACRE_SEPARATOR = 0,
    PASSACRE_CHARACTERS = 1,
    PASSACRE_WORDS = 2,
};

struct passacre_mb_state;

size_t passacre_mb_size(void);
size_t passacre_mb_align(void);
enum passacre_error_type passacre_mb_init(
    struct passacre_mb_state *);
enum passacre_error_type passacre_mb_required_bytes(
    struct passacre_mb_state *, size_t *);
enum passacre_error_type passacre_mb_entropy_bits(
    struct passacre_mb_state *, size_t *);
enum passacre_error_type passacre_mb_enable_shuffle(
    struct passacre_mb_state *);
enum passacre_error_type passacre_mb_add_base(
    struct passacre_mb_state *, enum passacre_mb_base,
    const unsigned char *, size_t);
enum passacre_error_type passacre_mb_add_sub_mb(
    struct passacre_mb_state *, struct passacre_mb_state *);
enum passacre_error_type passacre_mb_load_words_from_path(
    struct passacre_mb_state *, const unsigned char *, size_t);
enum passacre_error_type passacre_mb_encode_from_bytes(
    struct passacre_mb_state *,
    const unsigned char *, size_t, passacre_allocator, const void *);
enum passacre_error_type passacre_mb_finished(
    struct passacre_mb_state *);


enum passacre_gen_algorithm {
    PASSACRE_KECCAK = 0,
    PASSACRE_SKEIN = 1,
};

struct passacre_gen_state;

size_t passacre_gen_size(void);
size_t passacre_gen_align(void);
size_t passacre_gen_scrypt_buffer_size(void);
enum passacre_error_type passacre_gen_init(
    struct passacre_gen_state *, enum passacre_gen_algorithm);
enum passacre_error_type passacre_gen_use_scrypt(
    struct passacre_gen_state *,
    uint64_t, uint32_t, uint32_t, unsigned char *);
enum passacre_error_type passacre_gen_absorb_username_password_site(
    struct passacre_gen_state *, const unsigned char *, size_t,
    const unsigned char *, size_t, const unsigned char *, size_t);
enum passacre_error_type passacre_gen_absorb_null_rounds(
    struct passacre_gen_state *, size_t);
enum passacre_error_type passacre_gen_squeeze(
    struct passacre_gen_state *, unsigned char *, size_t);
enum passacre_error_type passacre_gen_squeeze_password(
    struct passacre_gen_state *, struct passacre_mb_state *,
    passacre_allocator, const void *);
enum passacre_error_type passacre_gen_finished(
    struct passacre_gen_state *);

size_t passacre_error(enum passacre_error_type, unsigned char *, size_t);

#endif
