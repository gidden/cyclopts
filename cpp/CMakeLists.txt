
INCLUDE_DIRECTORIES(
  "${CMAKE_CURRENT_SOURCE_DIR}"
  )

SET(
  CYCLOPTS_INCLUDE_DIRS ${CYCLOPTS_INCLUDE_DIRS}
  "${CMAKE_CURRENT_SOURCE_DIR}"
  PARENT_SCOPE
  )

FILE(GLOB src_files "${CMAKE_CURRENT_SOURCE_DIR}/*.cc")
SET(
  CYCLOPTS_SRC ${CYCLOPTS_SRC} ${src_files}
  PARENT_SCOPE
  )

SET(
  EXCHANGE_INSTANCE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/exchange_instance.cc"
  PARENT_SCOPE
  )

SET(
  PROBLEM_SRC "${CMAKE_CURRENT_SOURCE_DIR}/problem.cc"
  PARENT_SCOPE
  )

# c-level cyclopts tools 
#
# this is source for a separate library for any common tools used by other c
# interfaces. For example, consider two classes in separate translation units, A
# and B, with a base-derived class relationship. A_SRC and B_SRC should be set,
# and the files in A_SRC should also be added to CCYCLOPTS_SRC. A's module will
# then be compiled with A_SRC. B's module will be compiled with B_SRC *and then*
# linked agaisnt ccyclopts.
#
SET(
  CCYCLOPTS_SRC "${CMAKE_CURRENT_SOURCE_DIR}/problem.cc"
  PARENT_SCOPE
  )

FILE(GLOB header_files "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
INSTALL(
  FILES
  ${header_files}
  DESTINATION include/cyclopts
  COMPONENT cyclopts
)
