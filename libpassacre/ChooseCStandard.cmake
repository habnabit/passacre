# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

include(CheckCCompilerFlag)
include(CMakeParseArguments)


function (choose_c_standard)
  cmake_parse_arguments(CHOOSE_C_STANDARD "" "" "CHOICES" ${ARGN})
  foreach (STD ${CHOOSE_C_STANDARD_CHOICES})
    string(TOLOWER ${STD} LOWERSTD)
    set(STDFLAG "-std=${LOWERSTD}")
    check_c_compiler_flag("${STDFLAG}" HAVE_${STD})
    if (HAVE_${STD})
      add_definitions("${STDFLAG}")
      set(CMAKE_REQUIRED_FLAGS "${STDFLAG} ${CMAKE_REQUIRED_FLAGS}" PARENT_SCOPE)
      break ()
    endif ()
  endforeach ()
endfunction ()
