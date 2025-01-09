# LIMO Detector

This project aims to autonomously detect and count different coloured objects (red and green) in two worlds (basic_world.world & advanced_world.world), with ROS2 packeages and python files.

## Contents

**Maps:**

***Maps/map1.yaml*** (for the basic world)  
***worlds/map2.yaml*** (for the advanced world)

**Models**

***models/green_box***  
***models/red_box*** 

**Parametars**

***param/nav2_params.yaml*** (adjusted navigation parameters)

**RViz Configuration**

***RViz/adj_config.rviz*** (adjusted RViz configuration)

**Worlds:**

***worlds/basic_world.world*** (Red objects)  
***worlds/advanced_world.world*** (more red and green objects)

**Other Scripts:**

***cmp9767_tutorial/demo_inspection1*** (for autonomously move around the basic_world)  
***cmp9767_tutorial/demo_inspection2*** (for autonomously move around the advanced_world)  
***cmp9767_tutorial/detector_3d*** (objects detector)   
***cmp9767_tutorial/counter_3d*** (objects counter)   


## 1. Launch Gazebo

```bash
ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/<filename>
```

## 2. Launch Navigation

For running specific map and specific parameters

```bash 
ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/<filename>.yaml use_sim_time:=true params_file:=src/cmp9767_tutorial/params/nav2_params.yaml
```

## 3. Run the following commands in different terminals

``` bash 
ros2 run cmp9767_tutorial detector_3d
```

``` bash 
ros2 run cmp9767_tutorial counter_3d
```

``` bash 
ros2 run cmp9767_tutorial <filename>
```
