/*
The Keccak sponge function, designed by Guido Bertoni, Joan Daemen,
Michaël Peeters and Gilles Van Assche. For more information, feedback or
questions, please refer to our website: http://keccak.noekeon.org/

Implementation by the designers,
hereby denoted as "the implementer".

To the extent possible under law, the implementer has waived all copyright
and related or neighboring rights to the source code in this file.
http://creativecommons.org/publicdomain/zero/1.0/
*/

#include <stdio.h>
#include <string.h>
#include "brg_endian.h"
#include "displayIntermediateValues.h"
#include "KeccakNISTInterface.h"
#include "KeccakF-1600-interface.h"

typedef unsigned char UINT8;
typedef unsigned int UINT32;

#define nrRounds 24
UINT32 KeccakRoundConstants[nrRounds][2];
#define nrLanes 25
unsigned int KeccakRhoOffsets[nrLanes];

void KeccakPermutationOnWords(UINT32 *state);
void theta(UINT32 *A);
void rho(UINT32 *A);
void pi(UINT32 *A);
void chi(UINT32 *A);
void iota(UINT32 *A, unsigned int indexRound);

void toBitInterleaving(UINT32 low, UINT32 high, UINT32 *even, UINT32 *odd)
{
    unsigned int i;

    *even = 0;
    *odd = 0;
    for(i=0; i<64; i++) {
        unsigned int inBit;
        if (i < 32)
            inBit = (low >> i) & 1;
        else
            inBit = (high >> (i-32)) & 1;
        if ((i % 2) == 0)
            *even |= inBit << (i/2);
        else
            *odd |= inBit << ((i-1)/2);
    }
}

void fromBitInterleaving(UINT32 even, UINT32 odd, UINT32 *low, UINT32 *high)
{
    unsigned int i;

    *low = 0;
    *high = 0;
    for(i=0; i<64; i++) {
        unsigned int inBit;
        if ((i % 2) == 0)
            inBit = (even >> (i/2)) & 1;
        else
            inBit = (odd >> ((i-1)/2)) & 1;
        if (i < 32)
            *low |= inBit << i;
        else
            *high |= inBit << (i-32);
    }
}

void fromBytesToWords(UINT32 *stateAsWords, const unsigned char *state)
{
    unsigned int i, j;
    UINT32 low, high;
    UINT32 even, odd;

    for(i=0; i<(KeccakPermutationSize/64); i++) {
        low = 0;
        high = 0;
        for(j=0; j<(32/8); j++)
            low |= (UINT32)(state[i*(64/8)+j]) << (8*j);
        for(j=(32/8); j<(64/8); j++)
            high |= (UINT32)(state[i*(64/8)+j]) << (8*j-32);
        toBitInterleaving(low, high, &even, &odd);
        stateAsWords[2*i+0] = even;
        stateAsWords[2*i+1] = odd;
    }
}

void fromWordsToBytes(unsigned char *state, const UINT32 *stateAsWords)
{
    unsigned int i, j;
    UINT32 low, high;

    for(i=0; i<(KeccakPermutationSize/64); i++) {
        fromBitInterleaving(stateAsWords[2*i+0], stateAsWords[2*i+1], &low, &high);
        for(j=0; j<(32/8); j++)
            state[i*(64/8)+j] = (low >> (8*j)) & 0xFF;
        for(j=32/8; j<(64/8); j++)
            state[i*(64/8)+j] = (high >> (8*j-32)) & 0xFF;
    }
}

void KeccakPermutation(unsigned char *state)
{
    UINT32 stateAsWords[KeccakPermutationSize/32];

    displayStateAsBytes(1, "Input of permutation", state);
    fromBytesToWords(stateAsWords, state);
    KeccakPermutationOnWords(stateAsWords);
    fromWordsToBytes(state, stateAsWords);
    displayStateAsBytes(1, "State after permutation", state);
}

void KeccakPermutationAfterXor(unsigned char *state, const unsigned char *data, unsigned int dataLengthInBytes)
{
    unsigned int i;

    for(i=0; i<dataLengthInBytes; i++)
        state[i] ^= data[i];
    KeccakPermutation(state);
}

void KeccakPermutationOnWords(UINT32 *state)
{
    unsigned int i;

    displayStateAs32bitWords(3, "Same, with lanes as pairs of 32-bit words (bit interleaving)", state);

    for(i=0; i<nrRounds; i++) {
        displayRoundNumber(3, i);

        theta(state);
        displayStateAs32bitWords(3, "After theta", state);

        rho(state);
        displayStateAs32bitWords(3, "After rho", state);

        pi(state);
        displayStateAs32bitWords(3, "After pi", state);

        chi(state);
        displayStateAs32bitWords(3, "After chi", state);

        iota(state, i);
        displayStateAs32bitWords(3, "After iota", state);
    }
}

#define index(x, y,z) ((((x)%5)+5*((y)%5))*2 + z)
#define ROL32(a, offset) ((offset != 0) ? ((((UINT32)a) << offset) ^ (((UINT32)a) >> (32-offset))) : a)

void ROL64(UINT32 inEven, UINT32 inOdd, UINT32 *outEven, UINT32 *outOdd, unsigned int offset)
{
    if ((offset % 2) == 0) {
        *outEven = ROL32(inEven, offset/2);
        *outOdd = ROL32(inOdd, offset/2);
    }
    else {
        *outEven = ROL32(inOdd, (offset+1)/2);
        *outOdd = ROL32(inEven, (offset-1)/2);
    }
}

void theta(UINT32 *A)
{
    unsigned int x, y, z;
    UINT32 C[5][2], D[5][2];

    for(x=0; x<5; x++) {
        for(z=0; z<2; z++) {
            C[x][z] = 0; 
            for(y=0; y<5; y++)
                C[x][z] ^= A[index(x, y, z)];
        }
    }
    for(x=0; x<5; x++) {
        ROL64(C[(x+1)%5][0], C[(x+1)%5][1], &(D[x][0]), &(D[x][1]), 1);
        for(z=0; z<2; z++)
            D[x][z] ^= C[(x+4)%5][z];
    }
    for(x=0; x<5; x++)
        for(y=0; y<5; y++)
            for(z=0; z<2; z++)
                A[index(x, y, z)] ^= D[x][z];
}

void rho(UINT32 *A)
{
    unsigned int x, y;

    for(x=0; x<5; x++) for(y=0; y<5; y++)
        ROL64(A[index(x, y, 0)], A[index(x, y, 1)], &(A[index(x, y, 0)]), &(A[index(x, y, 1)]), KeccakRhoOffsets[5*y+x]);
}

void pi(UINT32 *A)
{
    unsigned int x, y, z;
    UINT32 tempA[50];

    for(x=0; x<5; x++) for(y=0; y<5; y++) for(z=0; z<2; z++)
        tempA[index(x, y, z)] = A[index(x, y, z)];
    for(x=0; x<5; x++) for(y=0; y<5; y++) for(z=0; z<2; z++)
        A[index(0*x+1*y, 2*x+3*y, z)] = tempA[index(x, y, z)];
}

void chi(UINT32 *A)
{
    unsigned int x, y, z;
    UINT32 C[5][2];

    for(y=0; y<5; y++) { 
        for(x=0; x<5; x++)
            for(z=0; z<2; z++)
                C[x][z] = A[index(x, y, z)] ^ ((~A[index(x+1, y, z)]) & A[index(x+2, y, z)]);
        for(x=0; x<5; x++)
            for(z=0; z<2; z++)
                A[index(x, y, z)] = C[x][z];
    }
}

void iota(UINT32 *A, unsigned int indexRound)
{
    A[index(0, 0, 0)] ^= KeccakRoundConstants[indexRound][0];
    A[index(0, 0, 1)] ^= KeccakRoundConstants[indexRound][1];
}

int LFSR86540(UINT8 *LFSR)
{
    int result = ((*LFSR) & 0x01) != 0;
    if (((*LFSR) & 0x80) != 0)
        // Primitive polynomial over GF(2): x^8+x^6+x^5+x^4+1
        (*LFSR) = ((*LFSR) << 1) ^ 0x71;
    else
        (*LFSR) <<= 1;
    return result;
}

void KeccakInitializeRoundConstants()
{
    UINT8 LFSRstate = 0x01;
    unsigned int i, j, bitPosition;
    UINT32 low, high;

    for(i=0; i<nrRounds; i++) {
        low = high = 0;
        for(j=0; j<7; j++) {
            bitPosition = (1<<j)-1; //2^j-1
            if (LFSR86540(&LFSRstate)) {
                if (bitPosition < 32)
                    low ^= (UINT32)1 << bitPosition;
                else
                    high ^= (UINT32)1 << (bitPosition-32);
            }
        }
        toBitInterleaving(low, high, &(KeccakRoundConstants[i][0]), &(KeccakRoundConstants[i][1]));
    }
}

void KeccakInitializeRhoOffsets()
{
    unsigned int x, y, t, newX, newY;

    KeccakRhoOffsets[0] = 0;
    x = 1;
    y = 0;
    for(t=0; t<24; t++) {
        KeccakRhoOffsets[5*y+x] = ((t+1)*(t+2)/2) % 64;
        newX = (0*x+1*y) % 5;
        newY = (2*x+3*y) % 5;
        x = newX;
        y = newY;
    }
}

void KeccakInitialize()
{
    KeccakInitializeRoundConstants();
    KeccakInitializeRhoOffsets();
}

void displayRoundConstants(FILE *f)
{
    unsigned int i;

    for(i=0; i<nrRounds; i++) {
        fprintf(f, "RC[%02i][0][0] = ", i);
        fprintf(f, "%08X:%08X", (unsigned int)(KeccakRoundConstants[i][0]), (unsigned int)(KeccakRoundConstants[i][1]));
        fprintf(f, "\n");
    }
    fprintf(f, "\n");
}

void displayRhoOffsets(FILE *f)
{
    unsigned int x, y;

    for(y=0; y<5; y++) for(x=0; x<5; x++) {
        fprintf(f, "RhoOffset[%i][%i] = ", x, y);
        fprintf(f, "%2i", KeccakRhoOffsets[5*y+x]);
        fprintf(f, "\n");
    }
    fprintf(f, "\n");
}

void KeccakInitializeState(unsigned char *state)
{
    memset(state, 0, KeccakPermutationSizeInBytes);
}

#ifdef ProvideFast576
void KeccakAbsorb576bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 72);
}
#endif

#ifdef ProvideFast832
void KeccakAbsorb832bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 104);
}
#endif

#ifdef ProvideFast1024
void KeccakAbsorb1024bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 128);
}
#endif

#ifdef ProvideFast1088
void KeccakAbsorb1088bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 136);
}
#endif

#ifdef ProvideFast1152
void KeccakAbsorb1152bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 144);
}
#endif

#ifdef ProvideFast1344
void KeccakAbsorb1344bits(unsigned char *state, const unsigned char *data)
{
    KeccakPermutationAfterXor(state, data, 168);
}
#endif

void KeccakAbsorb(unsigned char *state, const unsigned char *data, unsigned int laneCount)
{
    KeccakPermutationAfterXor(state, data, laneCount*8);
}

#ifdef ProvideFast1024
void KeccakExtract1024bits(const unsigned char *state, unsigned char *data)
{
    memcpy(data, state, 128);
}
#endif

void KeccakExtract(const unsigned char *state, unsigned char *data, unsigned int laneCount)
{
    memcpy(data, state, laneCount*8);
}
