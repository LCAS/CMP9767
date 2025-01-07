using this command to run the world in gazebo
    ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/myworld.world

using this command to run navigation package 
    ros2 launch limo_navigation limo_navigation.launch.py

using this command to run rqt gui
    ros2 run rqt_gui rqt_gui
        got to Plugins/Configuration/Dynamic Reconfigure, find the local costmap to adjust its parameters.
        Find the parameter for inflation_radius in the inflation_layer, change the value from 0.1 to 0.25. 

