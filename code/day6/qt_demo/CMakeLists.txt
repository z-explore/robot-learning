cmake_minimum_required(VERSION 3.16)
project(qt_demo LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt5 REQUIRED COMPONENTS Widgets)

add_executable(qt_demo 
    main.cpp    
    mainwindow.h
    mainwindow.cpp
    sensorworker.h
    sensorworker.cpp
)

target_link_libraries(qt_demo PRIVATE Qt5::Widgets)