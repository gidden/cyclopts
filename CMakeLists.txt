# This project name is cyclopts
PROJECT(cyclopts)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

# Direct any out-of-source builds to this directory
SET( CYCLOPTS_SOURCE_DIR ${CMAKE_SOURCE_DIR} )

# Tell CMake where the modules are
SET( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CYCLOPTS_SOURCE_DIR}/cmake )

# Use new Python library finder
find_package(PythonInterp REQUIRED)
find_package(PythonLibsNew REQUIRED)
message("-- PYTHON_EXECUTABLE: ${PYTHON_EXECUTABLE}")

# Find cyclus
FIND_PACKAGE( Cyclus REQUIRED )
SET(CYCLOPTS_INCLUDE_DIR ${CYCLOPTS_INCLUDE_DIR} ${CYCLUS_CORE_INCLUDE_DIR})
SET(LIBS ${LIBS} ${CYCLUS_CORE_LIBRARIES})

# include the model directories
SET(CYCLOPTS_INCLUDE_DIR ${CYCLOPTS_INCLUDE_DIR} src)

# include all the directories we just found
INCLUDE_DIRECTORIES( ${CYCLOPTS_INCLUDE_DIR} )

# This makes all the libraries build as SHARED
set(BUILD_SHARED_LIBS true)
message("-- CMake Install Prefix: ${CMAKE_INSTALL_PREFIX}")

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
ADD_SUBDIRECTORY(cyclopts)

get_property(inc_dirs DIRECTORY PROPERTY INCLUDE_DIRECTORIES)
message("-- C_INCLUDE_PATH for ${CMAKE_CURRENT_SOURCE_DIR}: ${inc_dirs}")

message("-- Copying C/C++ header files.")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/cpp/" DESTINATION
    "${CMAKE_BINARY_DIR}/cyclopts/include/" FILES_MATCHING PATTERN "*.h")

message("-- Copying Cython header files.")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/cyclopts/"
    DESTINATION "${CMAKE_BINARY_DIR}/cyclopts/"
    FILES_MATCHING PATTERN "*.pxd"
                   PATTERN "lib" EXCLUDE
                   PATTERN "include" EXCLUDE)

message("-- Copying scripts.")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/scripts/"
    DESTINATION "${CMAKE_BINARY_DIR}/scripts/"
    FILES_MATCHING PATTERN "*")

# # Build cyclopts_unit_tests
# ADD_EXECUTABLE( cyclopts_unit_tests ${CYCLOPTS_SRC} )
# TARGET_LINK_LIBRARIES( cyclopts_unit_tests dl ${LIBS} )

# INSTALL(
#   TARGETS cyclopts
#   RUNTIME DESTINATION bin
#   COMPONENT cyclopts
#   )

