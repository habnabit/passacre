# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

cmake_minimum_required(VERSION 2.8)
project(libpassacre)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/../version.txt" RAW_VERSION)
string(REPLACE "-" ";" SPLIT_VERSION "${RAW_VERSION}")
list(GET SPLIT_VERSION 0 VERSION)
list(GET SPLIT_VERSION 1 VERSION_COMMITS)
if ("${VERSION_COMMITS}" GREATER 0)
  set(VERSION "${VERSION}.post${VERSION_COMMITS}")
endif ()

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

include(FindPkgConfig QUIET)
if (PKG_CONFIG_FOUND)
  foreach (LIB ${CMAKE_C_IMPLICIT_LINK_LIBRARIES} ${PLATFORM_LIBS})
    set(PRIVATE_LIBS "${PRIVATE_LIBS} -l${LIB}")
  endforeach ()
  configure_file(libpassacre.pc.in libpassacre.pc @ONLY)
  install(FILES libpassacre.pc DESTINATION lib/pkgconfig)
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
