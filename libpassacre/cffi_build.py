# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import os

import cffi


libpassacre_build_dir = os.path.dirname(os.path.abspath(__file__))


def ffi_maker():
    ffi = cffi.FFI()
    ffi.set_source(
        'passacre._libpassacre_c',
        '#include "passacre.h"',
        include_dirs=[libpassacre_build_dir],
        extra_objects=[os.path.join(libpassacre_build_dir, 'libpassacre.a')])

    ffi.cdef("""

    typedef unsigned char *(*passacre_allocator)(size_t, const void *);

    enum passacre_error_type {
        PASSACRE_PANIC_ERROR,
        PASSACRE_KECCAK_ERROR,
        PASSACRE_SKEIN_ERROR,
        PASSACRE_SCRYPT_ERROR,
        PASSACRE_USER_ERROR,
        PASSACRE_INTERNAL_ERROR,
        PASSACRE_DOMAIN_ERROR,
        PASSACRE_ALLOCATOR_ERROR,
        ...
    };


    enum passacre_mb_base {
        PASSACRE_SEPARATOR,
        PASSACRE_CHARACTERS,
        PASSACRE_WORDS,
        ...
    };

    struct passacre_mb_state;

    size_t passacre_mb_size(void);
    size_t passacre_mb_align(void);
    enum passacre_error_type passacre_mb_init(
        struct passacre_mb_state *);
    enum passacre_error_type passacre_mb_required_bytes(
        struct passacre_mb_state *, size_t *);
    enum passacre_error_type passacre_mb_add_base(
        struct passacre_mb_state *, enum passacre_mb_base,
        const unsigned char *, size_t);
    enum passacre_error_type passacre_mb_load_words_from_path(
        struct passacre_mb_state *, const unsigned char *, size_t);
    enum passacre_error_type passacre_mb_encode_from_bytes(
        struct passacre_mb_state *,
        const unsigned char *, size_t, passacre_allocator, const void *);
    enum passacre_error_type passacre_mb_finished(
        struct passacre_mb_state *);


    enum passacre_gen_algorithm {
        PASSACRE_KECCAK,
        PASSACRE_SKEIN,
        ...
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


    size_t passacre_error(int, unsigned char *, size_t);

    """)

    return ffi
