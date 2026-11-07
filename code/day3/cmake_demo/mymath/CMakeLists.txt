add_library(mymath STATIC src/mymath.cpp)

target_include_directories(mymath PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)