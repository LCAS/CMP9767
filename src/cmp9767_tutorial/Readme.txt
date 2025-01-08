using this command to run the world in gazebo
    ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/myworld.world

using this command to run navigation package
    1. for running the defulat map
    ros2 launch limo_navigation limo_navigation.launch.py

    2. for running the my map
    ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/my_map.yaml use_sim_time:=true

    3. for running my map and my parameters
    ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/my_map.yaml use_sim_time:=true params_file:=src/cmp9767_tutorial/params/nav2_params.yaml

using this command to run rqt gui
    ros2 run rqt_gui rqt_gui
        got to Plugins/Configuration/Dynamic Reconfigure, find the local costmap to adjust its parameters.
        Find the parameter for inflation_radius in the inflation_layer, change the value from 0.1 to 0.25. 

a saved map for my_world world is saved in maps folder as my_map 
    it has the map of this folder in addition to the red boxes.
    
