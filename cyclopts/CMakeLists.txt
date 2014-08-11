# Python extension modules
include_directories(${CYCLOPTS_INCLUDE_DIRS})
include_directories("${CMAKE_CURRENT_SOURCE_DIR}")

# Print include dir
get_property(inc_dirs DIRECTORY PROPERTY INCLUDE_DIRECTORIES)
message("-- C_INCLUDE_PATH for ${CMAKE_CURRENT_SOURCE_DIR}: ${inc_dirs}")

# extra_types
set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/xdress_extra_types.pyx"
                            PROPERTIES CYTHON_IS_CXX TRUE)
cython_add_module(xdress_extra_types xdress_extra_types.pyx)

# dtypes
set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/dtypes.pyx"
                            PROPERTIES CYTHON_IS_CXX TRUE)
cython_add_module(dtypes dtypes.pyx)

# STL containers
# If the pyx file is a C++ file, we should specify that here.
# then, add the module
set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/stlcontainers.pyx"
                            PROPERTIES CYTHON_IS_CXX TRUE)
cython_add_module(stlcontainers stlcontainers.pyx)

# c-level cyclopts tools
ADD_LIBRARY(ccyclopts "${CCYCLOPTS_SRC}")
SET_TARGET_PROPERTIES(
  ccyclopts
  PROPERTIES
  INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
  INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"
  COMPONENT cyclopts
  LINKER_LANGUAGE CXX
  )

# problem
set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/problem.pyx"
                            PROPERTIES CYTHON_IS_CXX TRUE)
cython_add_module(problem problem.pyx ${PROBLEM_SRC})
target_link_libraries(problem dl ${LIBS})

# exchange_instance
set_source_files_properties("${PROJECT_SOURCE_DIR}/cyclopts/exchange_instance.pyx"
                            PROPERTIES CYTHON_IS_CXX TRUE)
cython_add_module(exchange_instance exchange_instance.pyx ${EXCHANGE_INSTANCE_SRC})
target_link_libraries(exchange_instance dl ${LIBS} ccyclopts)