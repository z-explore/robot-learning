find_package(Threads REQUIRED)

add_executable(app main.cpp producer_consumer/producer.cpp)
target_include_directories(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/producer_consumer)
target_link_libraries(app PRIVATE mymath Threads::Threads)
