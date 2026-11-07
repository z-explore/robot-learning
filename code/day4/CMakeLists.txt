cmake_minimum_required(VERSION 3.16)
project(day4 LANGUAGES CXX)

add_executable(crash crash.cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Threads REQUIRED)
