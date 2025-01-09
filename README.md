# LIMO Detector

This project aims to autonomously detect and count different coloured objects (red and green) in two worlds (basic_world.world & advanced_world.world), using ROS2 packages and python files that are compatable with LIMO Robot.

## Contents

**Maps:**   
***Maps/map1.yaml*** (for the basic world)  
***worlds/map2.yaml*** (for the advanced world)

**Models**  
***models/green_box*** (green object)  
***models/red_box*** (red object)

**Navigation Parametars**   
***param/nav2_params.yaml*** (adjusted navigation parameters)

**RViz Configuration**  
***RViz/adj_config.rviz*** (adjusted RViz configuration)

**Worlds:**     
***worlds/basic_world.world*** (few Red objects)  
***worlds/advanced_world.world*** (more red and green objects)

**Other Scripts:**  
***cmp9767_tutorial/basic_inspection***     (inspection file for the basic world)  
***cmp9767_tutorial/advanced_inspection***  (inspection file for the advanced world)  
***cmp9767_tutorial/detector_3d***          (objects detector)  
***cmp9767_tutorial/counter_3d***           (objects counter)  

## Setup
Build and Source the workspace using these commands:
```bash
colcon build --symlink-install
```
```bash
source install/setup.bash
```
## 1. Launch Gazebo
Using this command to run the world in gazebo
```bash
ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/<filename>
```
Example:
```bash
ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/basic_world
```

## 2. Launch Navigation

### 2.1 For running the default map
```bash 
ros2 launch limo_navigation limo_navigation.launch.py
```

### 2.2 For running specific map
```bash 
ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/my_map.yaml use_sim_time:=true
```

### 2.3 For running specific map and specific parameters
```bash 
ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/my_map.yaml use_sim_time:=true params_file:=src/cmp9767_tutorial/params/nav2_params.yaml
```

## 3. Run the detector file     
``` bash 
ros2 run cmp9767_tutorial detector_3d
```
## 4. Run the counter file
``` bash 
ros2 run cmp9767_tutorial counter_3d
```
## 5. Run the inspection file
``` bash 
ros2 run cmp9767_tutorial <filename>
```
Example:
``` bash 
ros2 run cmp9767_tutorial basic_inspection
```