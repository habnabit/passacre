# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

cmake_minimum_required(VERSION 2.8)
project(passacre)
set(CMAKE_C_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN 1)
include(GenerateExportHeader)

if (CMAKE_SIZEOF_VOID_P EQUAL 8)
  set(KECCAKF "keccak/KeccakF-1600-opt64.c")
elseif (CMAKE_SIZEOF_VOID_P EQUAL 4)
  set(KECCAKF "keccak/KeccakF-1600-opt32.c")
else ()
  message(FATAL_ERROR "I don't know how to pick which Keccak implementation to use!")
endif ()

add_definitions(-ggdb -O2)
add_library(passacre
            keccak/KeccakSponge.c ${KECCAKF}
            skein/skein.c skein/skeinBlockNo3F.c
            skein/threefish256Block.c skein/threefish512Block.c skein/threefish1024Block.c
            skein/skeinApi.c skein/threefishApi.c
            passacre.c)
set_target_properties(passacre PROPERTIES POSITION_INDEPENDENT_CODE ON)
generate_export_header(passacre)

install(FILES passacre.h passacre_export.h DESTINATION include)
install(TARGETS passacre
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)
