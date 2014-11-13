/*
 * Copyright (c) Aaron Gallagher <_@habnab.it>
 * See COPYING for details.
 */

#include <errno.h>
#include <string.h>
#include "passacre.h"
#include "keccak/KeccakSponge.h"
#include "skein/skeinApi.h"
#include "skein/threefishApi.h"


struct passacre_gen_state {
    enum passacre_gen_algorithm algorithm;
    unsigned char finished_absorbing;
    union {
        spongeState keccak;
        SkeinCtx_t skein;
        struct _skein_prng_state {
            ThreefishKey_t threefish;
            uint8_t buffer[64];
            unsigned char bytes_remaining;
        } skein_prng;
    } hasher;
};


size_t
passacre_gen_size(void)
{
    return sizeof (struct passacre_gen_state);
}


int
passacre_gen_init(struct passacre_gen_state *state, enum passacre_gen_algorithm algo)
{
    uint8_t nulls[64] = {0};
    memset(state, 0, sizeof *state);
    switch (algo) {
    case PASSACRE_KECCAK:
        if (InitSponge(&state->hasher.keccak, 64, 1536)) {
            return -EINVAL;
        }
        break;

    case PASSACRE_SKEIN:
        if (skeinCtxPrepare(&state->hasher.skein, Skein512) != SKEIN_SUCCESS) {
            return -EINVAL;
        }
        if (skeinInit(&state->hasher.skein, 512) != SKEIN_SUCCESS) {
            return -EINVAL;
        }
        if (skeinUpdate(&state->hasher.skein, nulls, 64) != SKEIN_SUCCESS) {
            return -EINVAL;
        }
        break;

    default:
        return -EINVAL;
    }

    state->algorithm = algo;
    return 0;
}


static int
passacre_gen_absorb(struct passacre_gen_state *state, const unsigned char *input, size_t n_bytes)
{
    if (state->finished_absorbing) {
        return -EINVAL;
    }
    switch (state->algorithm) {
    case PASSACRE_KECCAK:
        if (Absorb(&state->hasher.keccak, input, n_bytes * 8)) {
            return -EINVAL;
        }
        break;

    case PASSACRE_SKEIN:
        if (skeinUpdate(&state->hasher.skein, input, n_bytes) != SKEIN_SUCCESS) {
            return -EINVAL;
        }
        break;

    default:
        return -EINVAL;
    }

    return 0;
}


static const unsigned char PASSACRE_DELIMITER[1] = ":";


int
passacre_gen_absorb_username_password_site(
    struct passacre_gen_state *state,
    const unsigned char *username, size_t username_length,
    const unsigned char *password, size_t password_length,
    const unsigned char *site, size_t site_length)
{
    int result;
    if (username) {
        if ((result = passacre_gen_absorb(state, username, username_length))) {
            return result;
        }
        if ((result = passacre_gen_absorb(state, PASSACRE_DELIMITER, sizeof PASSACRE_DELIMITER))) {
            return result;
        }
    }
    if ((result = passacre_gen_absorb(state, password, password_length))) {
        return result;
    }
    if ((result = passacre_gen_absorb(state, PASSACRE_DELIMITER, sizeof PASSACRE_DELIMITER))) {
        return result;
    }
    if ((result = passacre_gen_absorb(state, site, site_length))) {
        return result;
    }
    return 0;
}


int
passacre_gen_absorb_null_rounds(struct passacre_gen_state *state, size_t n_rounds)
{
    int result;
    unsigned char nulls[1024] = {0};
    size_t i;
    for (i = 0; i < n_rounds; ++i) {
        if ((result = passacre_gen_absorb(state, nulls, sizeof nulls))) {
            return result;
        }
    }
    return 0;
}


int
passacre_gen_squeeze(struct passacre_gen_state *state, unsigned char *output, size_t n_bytes)
{
    int just_started = 0;
    uint8_t tweak[24] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x3f};
    if (!state->finished_absorbing) {
        state->finished_absorbing = just_started = 1;
    }
    switch (state->algorithm) {
    case PASSACRE_KECCAK:
        if (Squeeze(&state->hasher.keccak, output, n_bytes * 8)) {
            return -EINVAL;
        }
        break;

    case PASSACRE_SKEIN: {
        uint8_t input[64] = {0}, state_output[64];
        size_t i, half = n_bytes / 2, last_index = n_bytes - 1;
        unsigned char tmp, *output_start = output;
        struct _skein_prng_state *prng = &state->hasher.skein_prng;
        if (just_started) {
            uint8_t hash[64];
            if (skeinFinal(&state->hasher.skein, hash) != SKEIN_SUCCESS) {
                return -EINVAL;
            }
            threefishSetKey(&prng->threefish, Threefish512, (uint64_t *)hash, (uint64_t *)tweak);
            prng->bytes_remaining = 0;
        }
        while (n_bytes) {
            size_t to_copy = n_bytes > 64? 64 : n_bytes;
            if (!prng->bytes_remaining) {
                input[0] = 0;
                threefishEncryptBlockBytes(&prng->threefish, input, state_output);
                input[0] = 1;
                threefishEncryptBlockBytes(&prng->threefish, input, prng->buffer);
                threefishSetKey(&prng->threefish, Threefish512, (uint64_t *)state_output, (uint64_t *)tweak);
                prng->bytes_remaining = 64;
            }
            if (to_copy > prng->bytes_remaining) {
                to_copy = prng->bytes_remaining;
            }
            memcpy(output, prng->buffer + (64 - prng->bytes_remaining), to_copy);
            prng->bytes_remaining -= to_copy;
            n_bytes -= to_copy;
            output += to_copy;
        }
        /* reverse the bytes returned */
        for (i = 0; i < half; ++i) {
            tmp = output_start[i];
            output_start[i] = output_start[last_index - i];
            output_start[last_index - i] = tmp;
        }
        break;
    }

    default:
        return -EINVAL;
    }

    return 0;
}
