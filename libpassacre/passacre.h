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

enum passacre_gen_algorithm {
    PASSACRE_KECCAK = 0,
    PASSACRE_SKEIN = 1,
};

typedef unsigned char* (*AllocatorFn)(size_t , void const* );

typedef struct CPassacreContext CPassacreContext;

size_t passacre_ctx_size(void);

size_t passacre_ctx_align(void);

int passacre_ctx_init(CPassacreContext* ctx, AllocatorFn allocator_fn);

int passacre_ctx_describe_last_panic(CPassacreContext* ctx, void const* closure);

void passacre_ctx_finished(CPassacreContext* ctx);

typedef struct CMultiBase CMultiBase;

size_t passacre_mb_size(void);

size_t passacre_mb_align(void);

int passacre_mb_init(CPassacreContext* ctx, CMultiBase* mb);

int passacre_mb_required_bytes(CPassacreContext* ctx, CMultiBase const* mb, size_t* dest);

int passacre_mb_entropy_bits(CPassacreContext* ctx, CMultiBase const* mb, size_t* dest);

int passacre_mb_enable_shuffle(CPassacreContext* ctx, CMultiBase const* mb);

int passacre_mb_add_base(CPassacreContext* ctx, CMultiBase const* mb, unsigned int which, uint8_t const* string, size_t string_length);

int passacre_mb_add_sub_mb(CPassacreContext* ctx, CMultiBase const* parent, CMultiBase const* child);

int passacre_mb_load_words_from_path(CPassacreContext* ctx, CMultiBase const* mb, uint8_t const* path, size_t path_length);

int passacre_mb_encode_from_bytes(CPassacreContext* ctx, CMultiBase const* mb, uint8_t const* input, size_t input_length, void const* closure);

void passacre_mb_finished(CMultiBase* mb);

typedef struct CPassacreGenerator CPassacreGenerator;

size_t passacre_gen_size(void);

size_t passacre_gen_align(void);

size_t passacre_gen_scrypt_buffer_size(void);

int passacre_gen_init(CPassacreContext* ctx, CPassacreGenerator* gen, unsigned int algorithm);

int passacre_gen_use_scrypt(CPassacreContext* ctx, CPassacreGenerator const* gen, uint64_t n, uint32_t r, uint32_t p, uint8_t* persistence_buffer);

int passacre_gen_absorb_username_password_site(CPassacreContext* ctx, CPassacreGenerator const* gen, unsigned char const* username, size_t username_length, unsigned char const* password, size_t password_length, unsigned char const* site, size_t site_length);

int passacre_gen_absorb_null_rounds(CPassacreContext* ctx, CPassacreGenerator const* gen, size_t n_rounds);

int passacre_gen_squeeze(CPassacreContext* ctx, CPassacreGenerator const* gen, unsigned char* output, size_t output_length);

int passacre_gen_squeeze_password(CPassacreContext* ctx, CPassacreGenerator const* gen, CMultiBase const* mb, void const* closure);

void passacre_gen_finished(CPassacreGenerator* gen);

size_t passacre_error(int which, unsigned char* dest_p, size_t dest_length);

#endif
