# This project name is exchng_analysis
PROJECT(exchng_analysis)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

# Direct any out-of-source builds to this directory
SET( EXCHNG_ANALYSIS_SOURCE_DIR ${CMAKE_SOURCE_DIR} )

# Tell CMake where the modules are
SET( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${EXCHNG_ANALYSIS_SOURCE_DIR}/cmake )

# Find cycluscore
FIND_PACKAGE( cycluscore REQUIRED )
SET(EXCHNG_ANALYSIS_INCLUDE_DIR ${EXCHNG_ANALYSIS_INCLUDE_DIR} ${CYCLUS_CORE_INCLUDE_DIR})
SET(LIBS ${LIBS} ${CYCLUS_CORE_LIBRARIES})

# include the model directories
SET(EXCHNG_ANALYSIS_INCLUDE_DIR ${EXCHNG_ANALYSIS_INCLUDE_DIR} src)

# include all the directories we just found
INCLUDE_DIRECTORIES( ${EXCHNG_ANALYSIS_INCLUDE_DIR} )

# This makes all the libraries build as SHARED
set(BUILD_SHARED_LIBS true)
message("-- CMake Install Prefix: ${CMAKE_INSTALL_PREFIX}")

# Use new Python library finder
find_package(PythonInterp REQUIRED)
find_package(PythonLibsNew REQUIRED)
message("-- PYTHON_EXECUTABLE: ${PYTHON_EXECUTABLE}")

# Include the CMake script UseCython.cmake.  This defines add_cython_module().
# Instruction for use can be found at the top of cmake/UseCython.cmake.
include( UseCython )

# find numpy and include the numpy headers
find_package(Numpy REQUIRED)
include_directories("${NUMPY_INCLUDE_DIR}")

# With CMake, a clean separation can be made between the source tree and the
# build tree.  When all source is compiled, as with pure C/C++, the source is
# no-longer needed in the build tree.  However, with pure *.py source, the
# source is processed directly.  To handle this, we reproduce the availability
# of the source files in the build tree.
add_custom_target(ReplicatePythonSourceTree ALL "${CMAKE_COMMAND}" -P
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/ReplicatePythonSourceTree.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}"
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")

ADD_SUBDIRECTORY(cpp)
ADD_SUBDIRECTORY(analysis)

# # Build cycamore_unit_tests
# ADD_EXECUTABLE( exchng_analysis ${EXCHNG_ANALYSIS_SRC} )
# TARGET_LINK_LIBRARIES( exchng_analysis dl ${LIBS} )

# INSTALL(
#   TARGETS exchng_analysis
#   RUNTIME DESTINATION bin
#   COMPONENT exchng_analysis
#   )

