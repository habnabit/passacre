# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

cmake_minimum_required(VERSION 2.8)
project(libpassacre)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR})

file(READ "${CMAKE_SOURCE_DIR}/../version.txt" RAW_VERSION)
string(REPLACE "-" ";" SPLIT_VERSION "${RAW_VERSION}")
list(GET SPLIT_VERSION 0 VERSION)
list(GET SPLIT_VERSION 1 VERSION_COMMITS)
if (VERSION_COMMITS GREATER 0)
  set(VERSION "${VERSION}.post${VERSION_COMMITS}")
endif ()

if (DEFINED ENV{CMAKE_BUILD_TYPE})
  set(CMAKE_BUILD_TYPE "$ENV{CMAKE_BUILD_TYPE}")
  set(CMAKE_BUILD_TYPE "${CMAKE_BUILD_TYPE}" CACHE STRING "" FORCE)
endif ()

set(CMAKE_C_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN 1)

if (CMAKE_SIZEOF_VOID_P EQUAL 8)
  set(KECCAKF "keccak/KeccakF-1600-opt64.c")
elseif (CMAKE_SIZEOF_VOID_P EQUAL 4)
  set(KECCAKF "keccak/KeccakF-1600-opt32.c")
else ()
  message(FATAL_ERROR "I don't know how to pick which Keccak implementation to use!")
endif ()

include(CheckIncludeFiles)
include(CheckSymbolExists)
include(ChooseCStandard)
include(CMakeDependentOption)
choose_c_standard(CHOICES C11 C99)
check_include_files("emmintrin.h" HAVE_EMMINTRIN_H)
cmake_dependent_option(USE_SSE2 "Use optimized SSE2 code (for scrypt)." ON
                       "HAVE_EMMINTRIN_H" OFF)
check_include_files("sys/endian.h" HAVE_SYS_ENDIAN_H)
check_symbol_exists(be64enc "sys/endian.h" HAVE_DECL_BE64ENC)
check_symbol_exists(aligned_alloc "stdlib.h" HAVE_ALIGNED_ALLOC)
check_symbol_exists(posix_memalign "stdlib.h" HAVE_POSIX_MEMALIGN)
if (NOT HAVE_POSIX_MEMALIGN)
  message(STATUS "posix_memalign not found; trying with _POSIX_C_SOURCE set")
  set(POSIX_C_SOURCE "-D_POSIX_C_SOURCE=200112L")
  add_definitions("${POSIX_C_SOURCE}")
  set(CMAKE_REQUIRED_FLAGS "${POSIX_C_SOURCE} ${CMAKE_REQUIRED_FLAGS}")
  unset(HAVE_POSIX_MEMALIGN CACHE)
  check_symbol_exists(posix_memalign "stdlib.h" HAVE_POSIX_MEMALIGN)
  if (NOT HAVE_ALIGNED_ALLOC AND NOT HAVE_POSIX_MEMALIGN)
    message(FATAL_ERROR "no memory alignment function available")
  endif ()
endif ()
if (USE_SSE2)
  set(SCRYPTVER "sse")
else ()
  set(SCRYPTVER "nosse")
endif ()
configure_file("libpassacre-config.h.in" "${CMAKE_BINARY_DIR}/libpassacre-config.h")
include_directories("${CMAKE_BINARY_DIR}")

if (CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_CONFIGURATION_TYPES Debug Release)
  set(CMAKE_CONFIGURATION_TYPES "${CMAKE_CONFIGURATION_TYPES}" CACHE STRING "" FORCE)
endif ()

add_definitions(-pedantic -Wall -Wextra -Wunused -Werror)
set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -ggdb")
add_library(passacre_deps
            keccak/KeccakSponge.c ${KECCAKF}
            skein/skein.c skein/skeinBlockNo3F.c
            skein/threefish256Block.c skein/threefish512Block.c skein/threefish1024Block.c
            skein/skeinApi.c skein/threefishApi.c
            scrypt/sha256.c scrypt/crypto_scrypt-${SCRYPTVER}.c)
set_target_properties(passacre_deps PROPERTIES POSITION_INDEPENDENT_CODE ON)

if (CMAKE_BUILD_TYPE STREQUAL Release)
  set(CARGO_BUILD_FLAGS "--release")
  set(CARGO_BUILD_DIR "${CMAKE_SOURCE_DIR}/target/release")
else ()
  set(CARGO_BUILD_FLAGS "")
  set(CARGO_BUILD_DIR "${CMAKE_SOURCE_DIR}/target/debug")
endif ()

if ("$ENV{PASSACRE_LIBRARY_TESTING_ONLY}" STREQUAL yes)
  set(CARGO_BUILD_FLAGS "${CARGO_BUILD_FLAGS} --features testing-checks")
endif()

add_custom_target(passacre ALL
                  COMMAND env "CMAKE_BINARY_DIR=${CMAKE_BINARY_DIR}" sh -c
                  "cargo build ${CARGO_BUILD_FLAGS} 2>&1 | tee ${CMAKE_BINARY_DIR}/_cargo_out.txt"
                  COMMAND cp "${CARGO_BUILD_DIR}/libpassacre.a" "${CMAKE_BINARY_DIR}"
                  DEPENDS passacre_deps
                  VERBATIM
                  SOURCES src/lib.rs src/util.rs src/deps.rs src/passacre.rs src/c.rs)
list(APPEND TO_CLEAN target libpassacre.a)

set_directory_properties(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES "${TO_CLEAN}")
