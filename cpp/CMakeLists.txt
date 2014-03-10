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

ADD_SUBDIRECTORY(src)
ADD_SUBDIRECTORY(cli)

# Build cycamore_unit_tests
ADD_EXECUTABLE( exchng_analysis ${EXCHNG_ANALYSIS_SRC} )
TARGET_LINK_LIBRARIES( exchng_analysis dl ${LIBS} )

INSTALL(
  TARGETS exchng_analysis
  RUNTIME DESTINATION bin
  COMPONENT exchng_analysis
  )

