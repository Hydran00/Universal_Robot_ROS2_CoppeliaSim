# Copyright 2021 Stogl Robotics Consulting UG (haftungsbeschränkt)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
import xacro,os
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

distro = os.environ['ROS_DISTRO']
if distro == 'humble' or distro == 'galactic':
    spawner = "spawner"
else:  # foxy
    spawner = "spawner.py"


def generate_launch_description():
    # Declare arguments
    declared_arguments = []
    description_package = get_package_share_directory('coppeliasim_HWInterface')
    xacro_path = os.path.join(description_package,"urdf","ur.urdf.xacro")
    initial_joint_controllers = os.path.join(description_package,"config", "ur_controllers_coppelia.yaml")
    print(initial_joint_controllers)
    ur_type="ur3e"
    robot_description_content = xacro.process_file(xacro_path, mappings={"safety_limits":"true","safety_pos_margin":"0.15",
                                                                        "safety_k_position":"20",
                                                                        "name":"ur","ur_type":ur_type,
                                                                        "prefix":'',"sim_ignition":"false","sim_gazebo":"false",
                                                                        "simulation_controllers":initial_joint_controllers})
    robot_description_content = robot_description_content.toprettyxml(indent=' ')

    robot_description = {"robot_description": robot_description_content}

    robot_controllers = initial_joint_controllers

    # The actual simulation is a ROS2-control system interface.
    # Start that with the usual ROS2 controller manager mechanisms.
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        #prefix="screen -d -m gdb -command=/home/scherzin/.ros/my_debug_log --ex run --args",
        output="both",
        remappings=[
            ('motion_control_handle/target_frame', 'target_frame'),
            ('cartesian_motion_controller/target_frame', 'target_frame'),
            ]
    )

    # Joint states
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable=spawner,
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
    )
    
    cartesian_motion_controller_spawner = Node(
        package="controller_manager",
        executable=spawner,
        arguments=["cartesian_motion_controller", "-c", "/controller_manager"],
    )
    motion_control_handle_spawner = Node(
        package="controller_manager",
        executable=spawner,
        arguments=["motion_control_handle", "-c"," --stopped " "/controller_manager"],
    )

    
    # TF tree
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    # Visualization
    rviz_config = PathJoinSubstitution(
        [FindPackageShare("cartesian_controller_simulation"), "etc", "robot.rviz"]
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config]
    )

    # Nodes to start
    nodes = [
        control_node,
        joint_state_broadcaster_spawner,
        cartesian_motion_controller_spawner,
        motion_control_handle_spawner,
        robot_state_publisher,
        rviz,
    ]

    return LaunchDescription(declared_arguments + nodes)
