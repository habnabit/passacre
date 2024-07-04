/*
The Keccak sponge function, designed by Guido Bertoni, Joan Daemen,
Michaël Peeters and Gilles Van Assche. For more information, feedback or
questions, please refer to our website: http://keccak.noekeon.org/
*/


#include <stdio.h>

/************** Timing routine (for performance measurements) ***********/
/* By Doug Whiting */
/* unfortunately, this is generally assembly code and not very portable */
#if defined(_M_IX86) || defined(__i386) || defined(_i386) || defined(__i386__) || defined(i386) || \
    defined(_X86_)   || defined(__x86_64__) || defined(_M_X64) || defined(__x86_64)
#define _Is_X86_    1
#endif

#if  defined(_Is_X86_) && (!defined(__STRICT_ANSI__)) && (defined(__GNUC__) || !defined(__STDC__)) && \
    (defined(__BORLANDC__) || defined(_MSC_VER) || defined(__MINGW_H) || defined(__GNUC__))
#define HI_RES_CLK_OK         1          /* it's ok to use RDTSC opcode */

#if defined(_MSC_VER) // && defined(_M_X64)
#include <intrin.h>
#pragma intrinsic(__rdtsc)         /* use MSVC rdtsc call where defined */
#endif

#endif

typedef unsigned int uint_32t;

uint_32t HiResTime(void)           /* return the current value of time stamp counter */
    {
#if defined(HI_RES_CLK_OK)
    uint_32t x[2];
#if   defined(__BORLANDC__)
#define COMPILER_ID "BCC"
    __emit__(0x0F,0x31);           /* RDTSC instruction */
    _asm { mov x[0],eax };
#elif defined(_MSC_VER)
#define COMPILER_ID "MSC"
#if defined(_MSC_VER) // && defined(_M_X64)
    x[0] = (uint_32t) __rdtsc();
#else
    _asm { _emit 0fh }; _asm { _emit 031h };
    _asm { mov x[0],eax };
#endif
#elif defined(__MINGW_H) || defined(__GNUC__)
#define COMPILER_ID "GCC"
    asm volatile("rdtsc" : "=a"(x[0]), "=d"(x[1]));
#else
#error  "HI_RES_CLK_OK -- but no assembler code for this platform (?)"
#endif
    return x[0];
#else
    /* avoid annoying MSVC 9.0 compiler warning #4720 in ANSI mode! */
#if (!defined(_MSC_VER)) || (!defined(__STDC__)) || (_MSC_VER < 1300)
    FatalError("No support for RDTSC on this CPU platform\n");
#endif
    return 0;
#endif /* defined(HI_RES_CLK_OK) */
    }

#define TIMER_SAMPLE_CNT (100)

uint_32t calibrate()
{
    uint_32t dtMin = 0xFFFFFFFF;        /* big number to start */
    uint_32t t0,t1,i;

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        t1 = HiResTime();
        if (dtMin > t1-t0)              /* keep only the minimum time */
            dtMin = t1-t0;
        }
    return dtMin;
}

#include "KeccakF-1600-interface.h"
#include "KeccakNISTInterface.h"

uint_32t measureKeccakAbsorb1024bits(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    ALIGN unsigned char state[KeccakPermutationSizeInBytes];
    ALIGN unsigned char input[128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
#ifdef ProvideFast1024
        KeccakAbsorb1024bits(state, input);
#else
        KeccakAbsorb(state, input, 1024/64);
#endif
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakAbsorb1088bits(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    ALIGN unsigned char state[KeccakPermutationSizeInBytes];
    ALIGN unsigned char input[136];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
#ifdef ProvideFast1088
        KeccakAbsorb1088bits(state, input);
#else
        KeccakAbsorb(state, input, 1088/64);
#endif
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakAbsorb1344bits(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    ALIGN unsigned char state[KeccakPermutationSizeInBytes];
    ALIGN unsigned char input[200];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
#ifdef ProvideFast1344
        KeccakAbsorb1344bits(state, input);
#else
        KeccakAbsorb(state, input, 1344/64);
#endif
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakAbsorb(uint_32t dtMin, unsigned int laneCount)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    ALIGN unsigned char state[KeccakPermutationSizeInBytes];
    ALIGN unsigned char input[64];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        KeccakAbsorb(state, input, laneCount);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakPermutation(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    ALIGN unsigned char state[KeccakPermutationSizeInBytes];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        KeccakPermutation(state);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash1block(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash2blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[256];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 1024+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash3blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[384];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 2048+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash10blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[10*128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 9*1024+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash30blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[30*128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 29*1024+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash100blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[100*128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 99*1024+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

uint_32t measureKeccakHash1000blocks(uint_32t dtMin)
{
    uint_32t tMin = 0xFFFFFFFF;         /* big number to start */
    uint_32t t0,t1,i;
    hashState state;
    ALIGN unsigned char data[1000*128];

    for (i=0;i < TIMER_SAMPLE_CNT;i++)  /* calibrate the overhead for measuring time */
        {
        t0 = HiResTime();
        Init(&state, 0);
        Update(&state, data, 999*1024+29);
        Final(&state, 0);
        t1 = HiResTime();
        if (tMin > t1-t0 - dtMin)       /* keep only the minimum time */
            tMin = t1-t0 - dtMin;
        }

    /* now tMin = # clocks required for running RoutineToBeTimed() */
    
    return tMin;
}

void doTiming()
{
    uint_32t calibration;
    uint_32t measurementKeccakPermutation;
    uint_32t measurementKeccakAbsorb1024bits;
    uint_32t measurementKeccakAbsorb1088bits;
    uint_32t measurementKeccakAbsorb1344bits;
    uint_32t measurementKeccakAbsorb;
    uint_32t measurementKeccakHash1block;
    uint_32t measurementKeccakHash2blocks;
    uint_32t measurementKeccakHash3blocks;
    uint_32t measurementKeccakHash10blocks;
    uint_32t measurementKeccakHash30blocks;
    uint_32t measurementKeccakHash100blocks;
    uint_32t measurementKeccakHash1000blocks;
    
    calibration = calibrate();

    measurementKeccakPermutation = measureKeccakPermutation(calibration);
    printf("Cycles for KeccakPermutation(state): %d\n", measurementKeccakPermutation);
    printf("Cycles per byte for rate 1024: %f\n", measurementKeccakPermutation/128.0);
    printf("\n");

    measurementKeccakAbsorb1024bits = measureKeccakAbsorb1024bits(calibration);
    printf("Cycles for KeccakAbsorb1024bits(state, input): %d\n", measurementKeccakAbsorb1024bits);
    printf("Cycles per byte for rate 1024: %f\n", measurementKeccakAbsorb1024bits/128.0);
    printf("\n");

    measurementKeccakAbsorb1088bits = measureKeccakAbsorb1088bits(calibration);
    printf("Cycles for KeccakAbsorb1088bits(state, input): %d\n", measurementKeccakAbsorb1088bits);
    printf("Cycles per byte for rate 1088: %f\n", measurementKeccakAbsorb1088bits/136.0);
    printf("\n");

    measurementKeccakAbsorb1344bits = measureKeccakAbsorb1344bits(calibration);
    printf("Cycles for KeccakAbsorb1344bits(state, input): %d\n", measurementKeccakAbsorb1344bits);
    printf("Cycles per byte for rate 1344: %f\n", measurementKeccakAbsorb1344bits/168.0);
    printf("\n");

    measurementKeccakAbsorb = measureKeccakAbsorb(calibration, 18);
    printf("Cycles for KeccakAbsorb(state, input, 1152bits): %d\n", measurementKeccakAbsorb);
    printf("Cycles per byte for rate 1152: %f\n", measurementKeccakAbsorb/144.0);
    measurementKeccakAbsorb = measureKeccakAbsorb(calibration, 13);
    printf("Cycles for KeccakAbsorb(state, input, 832bits): %d\n", measurementKeccakAbsorb);
    printf("Cycles per byte for rate 832: %f\n", measurementKeccakAbsorb/104.0);
    measurementKeccakAbsorb = measureKeccakAbsorb(calibration, 9);
    printf("Cycles for KeccakAbsorb(state, input, 576bits): %d\n", measurementKeccakAbsorb);
    printf("Cycles per byte for rate 576: %f\n", measurementKeccakAbsorb/72.0);
    printf("\n");

    measurementKeccakHash1block = measureKeccakHash1block(calibration);
    printf("Cycles for Init, Update, Finalize (1 block): %d\n", measurementKeccakHash1block);
    printf("\n");

    measurementKeccakHash2blocks = measureKeccakHash2blocks(calibration);
    printf("Cycles for Init, Update, Finalize (2 blocks): %d\n", measurementKeccakHash2blocks);
    printf("\n");

    measurementKeccakHash3blocks = measureKeccakHash3blocks(calibration);
    printf("Cycles for Init, Update, Finalize (3 blocks): %d\n", measurementKeccakHash3blocks);
    printf("\n");

    measurementKeccakHash10blocks = measureKeccakHash10blocks(calibration);
    printf("Cycles for Init, Update, Finalize (10 blocks): %d\n", measurementKeccakHash10blocks);
    printf("\n");

    measurementKeccakHash30blocks = measureKeccakHash30blocks(calibration);
    printf("Cycles for Init, Update, Finalize (30 blocks): %d\n", measurementKeccakHash30blocks);
    printf("\n");

    measurementKeccakHash100blocks = measureKeccakHash100blocks(calibration);
    printf("Cycles for Init, Update, Finalize (100 blocks): %d\n", measurementKeccakHash100blocks);
    printf("\n");

    measurementKeccakHash1000blocks = measureKeccakHash1000blocks(calibration);
    printf("Cycles for Init, Update, Finalize (1000 blocks): %d\n", measurementKeccakHash1000blocks);
    printf("\n");
}
