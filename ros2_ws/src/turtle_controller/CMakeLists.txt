cmake_minimum_required(VERSION 3.8)
project(turtle_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)
find_package(robot_interfaces REQUIRED)

add_executable(circle_publisher src/circle_publisher.cpp)
add_executable(pose_listener src/pose_listener.cpp)
add_executable(square_walker src/square_walker.cpp)
add_executable(status_publisher src/status_publisher.cpp)
add_executable(status_monitor src/status_monitor.cpp)
add_executable(rotate_client src/rotate_client.cpp)
ament_target_dependencies(circle_publisher rclcpp geometry_msgs)
ament_target_dependencies(pose_listener rclcpp turtlesim)
ament_target_dependencies(square_walker rclcpp geometry_msgs turtlesim)
ament_target_dependencies(status_publisher rclcpp geometry_msgs robot_interfaces)
ament_target_dependencies(status_monitor rclcpp robot_interfaces)
ament_target_dependencies(rotate_client rclcpp rclcpp_action turtlesim)
install(TARGETS circle_publisher pose_listener square_walker status_publisher status_monitor rotate_client DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()