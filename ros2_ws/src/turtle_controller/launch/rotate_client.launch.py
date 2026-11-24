from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtle_controller',
            executable='rotate_client',
            name='rotate_client'
        ),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim_node'
        )
    ])