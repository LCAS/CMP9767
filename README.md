# Robot Programming Assessment

## 1.Launching the Simulation in Gazebo
### 1.1 Run the Default World 
```bash
ros2 launch limo_gazebosim limo_gazebo_diff.launch.py              
```
### 1.2 Run my Custom World
```bash
 ros2 launch limo_gazebosim limo_gazebo_diff.launch.py world:=src/cmp9767_tutorial/worlds/testworld.world
```
## 2.Running Robot Navigation
### 2.1 Use the Default Map
```bash
ros2 launch limo_navigation limo_navigation.launch.py
```
### 2.2 Run my Custom Map
```bash
ros2 launch limo_navigation limo_navigation.launch.py map:=src/cmp9767_tutorial/maps/my_map.yaml use_sim_time:=true
```
## 3.Building and Running Python Code (Run this before any Python files)

### 3.1 Build the Robot Software
```bash
colcon build --symlink-install
```
### 3.2 Set Up the Environment
```bash
source install/setup.bash
```
## 4. Running Robot Functionality Scripts 
### 4.1 Run Robot Autonomously (demo_inspection.py)
```bash
ros2 run cmp9767_tutorial demo_inspection
```
### 4.2 Detect Object Colors (detector_3d.py)
```bash
ros2 run cmp9767_tutorial detector_3d
```
### 4.3 Count Colored Objects (counter_3d.py)
 ```bash
ros2 run cmp9767_tutorial counter_3d 
```
