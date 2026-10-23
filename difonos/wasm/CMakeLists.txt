cmake_minimum_required(VERSION 3.20)
project(difonos_espeak_wasm C)

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(COMPILE_INTONATIONS OFF CACHE BOOL "" FORCE)
set(ENABLE_TESTS OFF CACHE BOOL "" FORCE)
set(USE_MBROLA OFF CACHE BOOL "" FORCE)
set(USE_LIBSONIC OFF CACHE BOOL "" FORCE)
set(USE_LIBPCAUDIO OFF CACHE BOOL "" FORCE)
set(USE_SPEECHPLAYER OFF CACHE BOOL "" FORCE)
set(USE_ASYNC OFF CACHE BOOL "" FORCE)
set(USE_KLATT OFF CACHE BOOL "" FORCE)

add_subdirectory(../vendor/espeak-ng espeak-ng-build EXCLUDE_FROM_ALL)

add_executable(difonos-espeak-en phonemizer.c)
target_link_libraries(difonos-espeak-en PRIVATE espeak-ng)
target_include_directories(difonos-espeak-en PRIVATE ../vendor/espeak-ng/src/include)
set(DIFONOS_WASM_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../runtime/espeak-wasm")
file(MAKE_DIRECTORY "${DIFONOS_WASM_OUTPUT_DIR}")
set_target_properties(difonos-espeak-en PROPERTIES
  SUFFIX ".js"
  RUNTIME_OUTPUT_DIRECTORY "${DIFONOS_WASM_OUTPUT_DIR}"
)
if(NOT ESPEAK_DATA_DIR)
  set(ESPEAK_DATA_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../vendor/espeak-ng-wasm/data")
endif()
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/espeak-ng-data")
file(COPY "${ESPEAK_DATA_DIR}/" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}/espeak-ng-data")
target_link_options(difonos-espeak-en PRIVATE
  "-sMODULARIZE=1"
  "-sEXPORT_NAME=createDifonosEspeak"
  "-sENVIRONMENT=web,node"
  "-sINVOKE_RUN=0"
  "-sALLOW_MEMORY_GROWTH=1"
  "-sEXPORTED_FUNCTIONS=['_difonos_phonemize','_malloc','_free']"
  "-sEXPORTED_RUNTIME_METHODS=['UTF8ToString','stringToUTF8','lengthBytesUTF8']"
  "--preload-file" "espeak-ng-data@/espeak-ng-data"
)
