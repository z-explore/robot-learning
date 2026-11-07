cmake_minimum_required(VERSION 3.16)
project(cmake_demo LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMARK_CXX_STANDARD_REQUIRED ON)

add_subdirectory(mymath)
add_subdirectory(app)
