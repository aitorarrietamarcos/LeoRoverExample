# LeoRover Visual Marker Following

`leo_night_marker` is a ROS 1 catkin package for detecting an ALVAR visual marker and steering a LeoRover towards it. It provides a diagnostic monitor, a basic follower, and a follower that briefly rotates to reacquire a lost marker.

The package contains the marker-tracking and following logic. The rover driver, camera driver, camera calibration, and robot transforms must be provided by the existing LeoRover setup. Despite the package name, no dedicated night-vision or low-light enhancement is implemented.

## Features

- Detect visual markers using `ar_track_alvar`.
- Track marker ID `0` by default.
- Turn to align with the marker, then drive forward towards it.
- Stop when the marker is close enough or detections become stale.
- Optionally rotate for up to 10 seconds after losing a previously detected marker.
- Monitor marker positions and intended actions without publishing movement commands.

## Connect to the LeoRover and locate the project

### 1. Power on and join the rover Wi-Fi

Power on the LeoRover and connect your laptop to its Wi-Fi network. Use the network name and credentials provided by the rover owner. The address used in this setup is `10.0.0.1`.

### 2. Open an SSH session from your laptop

Open Terminal on your Mac, or another SSH-capable terminal on your laptop:

```bash
ssh pi@10.0.0.1
```

For a first connection, confirm the host fingerprint with the rover owner before accepting it. Enter the password for the rover's `pi` account when prompted. Password characters are not displayed as you type.

After connecting, a prompt such as `pi@leo:~$` means commands now run **on the rover**. Run this in every new SSH terminal:

```bash
cd ~/ros_ws
source devel/setup.bash
```

### 3. Locate the program

The project package lives on the Raspberry Pi at:

```text
/home/pi/ros_ws/src/leo_night_marker/
```

The Python programs are in its `scripts/` folder. The detector launch file is in `launch/`, and its YAML configuration is in `config/`.

```bash
cd ~/ros_ws/src/leo_night_marker
ls -la
ls -l scripts/
rospack find leo_night_marker
```

To view or edit a script:

```bash
nano ~/ros_ws/src/leo_night_marker/scripts/marker_follower_search.py
```

In nano, save with `Ctrl+O`, press Enter to confirm the filename, and exit with `Ctrl+X`. Use spaces for Python indentation. Changes to a running script take effect after you stop and restart it.

### 4. Start the existing project in two SSH terminals

The existing installation does not need rebuilding just to run it or change Python constants. Follow the Installation section only when setting up a new workspace or resolving missing dependencies.

**Terminal 1 — keep the detector running:**

```bash
ssh pi@10.0.0.1
cd ~/ros_ws
source devel/setup.bash
roslaunch leo_night_marker artag_tracker.launch
```

**Terminal 2 — verify detection and run the monitor:**

```bash
ssh pi@10.0.0.1
cd ~/ros_ws
source devel/setup.bash
rostopic echo -n 1 /ar_pose_marker
python3 ~/ros_ws/src/leo_night_marker/scripts/marker_monitor.py
```

Show the ALVAR tag to the camera. A non-empty `markers` list indicates a detection. `markers: []` means no marker was recognised in that message. Stop the monitor with `Ctrl+C` before running a follower.

**The supplied followers have `DRY_RUN = False`. Edit the selected script to `DRY_RUN = True` before the first test.** Then run exactly one version in Terminal 2:

```bash
# Basic follower
python3 ~/ros_ws/src/leo_night_marker/scripts/marker_follower.py
```

Or:

```bash
# Follower with a bounded search turn
python3 ~/ros_ws/src/leo_night_marker/scripts/marker_follower_search.py
```

Check the printed actions before enabling motion. To move the rover, stop the follower, set `DRY_RUN = False`, and restart that same script in a clear, supervised area. Keep Terminal 1 running throughout.

### 5. Camera view and optional night settings

From a browser on the laptop connected to the rover Wi-Fi, open:

```text
http://10.0.0.1:8080/stream?topic=/camera/image_raw&type=ros_compressed
```

This URL relies on the streaming service already configured on the rover. It is not provided by this package.

If the existing camera node is `/raspicam_node`, the night settings previously used in this setup can be applied from an SSH terminal:

```bash
rosrun dynamic_reconfigure dynparam set /raspicam_node \
  "{exposure_mode: night, shutter_speed: 0, ISO: 1600, exposure_compensation: 4, contrast: 0, brightness: 60}"
```

Apply these only when appropriate for the current lighting. A restart may reset camera settings. Check image sharpness and detection before moving.

### 6. Stop and disconnect

Press `Ctrl+C` in Terminal 2 to stop the follower. Confirm the rover has stopped before closing the connection or using another controller. Stop the tracker in Terminal 1 with `Ctrl+C` when finished. Type `exit` in each SSH terminal to return to the laptop shell.

### Copy the project from the rover to your laptop

Run the following **in a local laptop terminal**, not inside SSH. These commands copy the package source without removing it from the rover:

```bash
mkdir -p ~/Projects/leorover-innoguard
scp -r pi@10.0.0.1:/home/pi/ros_ws/src/leo_night_marker \
  ~/Projects/leorover-innoguard/
```

On a Mac, open the copied folder with:

```bash
open ~/Projects/leorover-innoguard
```

The local copy is for inspection, editing and version control. Running ROS scripts directly on the laptop still requires a compatible ROS environment and access to the rover's ROS interfaces. Downloading the source does not install those dependencies.

## Project files

| File | Purpose |
| --- | --- |
| `launch/artag_tracker.launch` | Starts the marker detector and remaps camera topics. |
| `config/artag.yaml` | Marker size, tracking thresholds, frequency, and output frame. |
| `scripts/marker_monitor.py` | Logs marker positions and intended actions; does not control the rover. |
| `scripts/marker_follower.py` | Follows the target marker and stops when it is lost. |
| `scripts/marker_follower_search.py` | Follows the target marker and searches briefly after losing it. |
| `package.xml` | Catkin package metadata and dependencies. |
| `CMakeLists.txt` | Catkin build configuration. |
| `src/` | Currently empty. |

The supplied archive also contains `launch/artag_tracker.launch>` and a Python `__pycache__` directory. Use `artag_tracker.launch` without the trailing `>`; the duplicate file and generated bytecode are not needed for normal use.

## Requirements

- A ROS 1 environment with catkin and Python 3-compatible `rospy`.
- ROS packages: `ar_track_alvar`, `ar_track_alvar_msgs`, `geometry_msgs`, and `rospy`.
- A calibrated camera publishing image and camera-info messages.
- A valid TF transform from the camera frame to `base_link`.
- A LeoRover base controller accepting `geometry_msgs/Twist` on `/cmd_vel`.
- An ALVAR marker matching the configured ID and physical size.

The project has been used on the existing LeoRover ROS Noetic setup. Its workspace is `~/ros_ws` on the rover. The package source itself does not enforce a ROS distribution. If your rover uses another workspace, adjust the paths below.

## Installation

Place the package folder in the workspace's `src` directory:

```text
~/ros_ws/src/leo_night_marker/
```

In a terminal with your ROS environment sourced, install declared dependencies and build:

```bash
cd ~/ros_ws
rosdep install --from-paths src --ignore-src -r -y
chmod +x src/leo_night_marker/scripts/*.py
catkin_make
source devel/setup.bash
rospack find leo_night_marker
```

`rosdep` must already be initialized. Source `~/ros_ws/devel/setup.bash` in every terminal used below. The current CMake configuration does not install the Python scripts or launch/config files, so these instructions run the package from its source workspace rather than an install space.

## Before moving the rover

**Both follower scripts currently set `DRY_RUN = False`, so starting either follower can move the rover immediately.** Begin with the monitor, or edit the selected follower to set `DRY_RUN = True` before running it.

Use a clear, supervised test area and keep the rover's stop control accessible. There is no obstacle detection or collision avoidance. Run only one follower and avoid other controllers publishing to `/cmd_vel` at the same time.

The follower uses a nominal target distance of `0.10 m`, with an effective forward-motion threshold of `0.18 m`. These distances refer to the reported marker position in `base_link`, not clearance from the rover's front edge. Check your robot geometry and choose a suitable distance before enabling movement.

## Running the project

### 1. Start the existing rover and camera stack

Start the LeoRover base, camera, and TF publishers using your existing rover setup. Their startup launch files are not included in this package. Ensure a ROS master is running; use `roscore` in a separate terminal only if the existing stack does not already start one.

Check the default camera topics:

```bash
rostopic hz /camera/image_raw
rostopic echo -n 1 /camera/camera_info
```

### 2. Start marker detection

```bash
roslaunch leo_night_marker artag_tracker.launch
```

If the camera uses different topics, override the launch arguments:

```bash
roslaunch leo_night_marker artag_tracker.launch \
  cam_image_topic:=/your_camera/image_raw \
  cam_info_topic:=/your_camera/camera_info
```

Show the target marker to the camera and inspect the detector output:

```bash
rostopic echo /ar_pose_marker
```

### 3. Check detection without moving

In another sourced terminal:

```bash
rosrun leo_night_marker marker_monitor.py
```

The monitor prints the target's `x`, `y`, and `z` position and an intended action. Its thresholds differ from those of the followers: it uses a `0.65 m` target distance and a `0.12 m` lateral tolerance. It is a diagnostic aid, not an exact preview of the current follower configuration.

### 4. Run one follower

Basic follower, which stops after losing the tag:

```bash
rosrun leo_night_marker marker_follower.py
```

Alternatively, run the follower with temporary reacquisition:

```bash
rosrun leo_night_marker marker_follower_search.py
```

The search follower waits motionless until the target has been seen at least once. It does not explore the environment or search for a never-seen tag.

### 5. Stop

Press `Ctrl+C` in the follower terminal. Both followers attempt to publish a zero-velocity command in their `finally` block on normal exit. This cannot guarantee a stop after a process crash, power loss, or network failure; the rover controller should enforce its own command timeout.

Even with `DRY_RUN = True`, the followers publish a single zero-velocity command on exit. The monitor never publishes to `/cmd_vel`.

## How following works

Each script reads `/ar_pose_marker`, selects the configured marker ID, and stores its latest position and local receipt time. Decisions run at 10 Hz.

The controller assumes the reported position uses the `base_link` convention: `x` forward, `y` left, and `z` upward. The detector is configured to output that frame; the follower itself does not transform or validate incoming poses.

When the target was received within the last `0.5 s`, the follower applies these rules in order:

1. If `y > 0.08 m`, turn left in place.
2. If `y < -0.08 m`, turn right in place.
3. Otherwise, if `x > 0.18 m`, drive forward.
4. Otherwise, stop.

Turning takes priority over approaching. The controller uses fixed speeds, does not reverse, and does not use `z` or marker orientation.

| Target state | Basic follower | Search follower |
| --- | --- | --- |
| Never seen | Stop | Stop |
| Last seen at most 0.5 s ago | Follow using the rules above | Follow using the rules above |
| Last seen more than 0.5 s but at most 10.5 s ago | Stop | Rotate at `+0.35 rad/s` |
| Last seen more than 10.5 s ago | Stop | Stop |
| Reacquired | Resume following | Resume following |

An empty detection message does not immediately clear the stored position: the scripts keep using it until the receipt-time timeout expires. Reaching the target does not terminate the node; it continues monitoring and can move again if the marker moves.

## Configuration

### Detector: `config/artag.yaml`

| Setting | Current value | Meaning |
| --- | --- | --- |
| `marker_size` | `5.0` | ALVAR marker size in centimetres; match the physical marker square shown on paper or a screen. |
| `max_new_marker_error` | `0.08` | New-marker detection error threshold. |
| `max_track_error` | `0.2` | Tracking error threshold. |
| `max_frequency` | `8.0` | Configured maximum tracking frequency, in Hz. |
| `output_frame` | `base_link` | Frame used for marker poses. |

### Followers: constants at the top of each script

These settings are hard-coded Python constants, not ROS parameters. Edit the appropriate file and restart the node after changes.

| Constant | Basic follower | Search follower | Unit / role |
| --- | --- | --- | --- |
| `TARGET_ID` | `0` | `0` | Marker ID |
| `TARGET_DISTANCE` | `0.10` | `0.10` | Metres |
| `DISTANCE_TOLERANCE` | `0.08` | `0.08` | Added to target distance for the forward threshold |
| `LATERAL_TOLERANCE` | `0.08` | `0.08` | Metres |
| `LOST_TIMEOUT` | `0.5` | `0.5` | Seconds since last target receipt |
| `FORWARD_SPEED` | `0.20` | `0.18` | Metres per second |
| `TURN_SPEED` | `0.70` | `0.70` | Radians per second |
| `DRY_RUN` | `False` | `False` | Suppresses loop command publishing when `True` |
| `SEARCH_DURATION` | — | `10.0` | Seconds after the loss timeout |
| `SEARCH_TURN_SPEED` | — | `0.35` | Radians per second |

## ROS interfaces

| Topic | Message type | Usage |
| --- | --- | --- |
| `/camera/image_raw` | `sensor_msgs/Image` | Default detector image input; configurable launch argument. |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | Default detector calibration input; configurable launch argument. |
| `/ar_pose_marker` | `ar_track_alvar_msgs/AlvarMarkers` | Detector output consumed by all three scripts. |
| `/cmd_vel` | `geometry_msgs/Twist` | Movement commands from either follower. |

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| Package not found | Confirm the package is in the workspace's `src`, build it, and source `devel/setup.bash`. |
| Script not found or permission denied | Make the Python scripts executable and run from the sourced source workspace. |
| Missing Python/ROS imports | Check the ROS environment and install the dependencies declared in `package.xml`. |
| No markers detected | Check image and camera-info topics, calibration, marker size/type, lighting, and visibility. |
| Transform errors or incorrect steering | Verify camera-to-`base_link` TF and inspect the marker message's frame and coordinate signs. |
| Monitor sees a tag but follower waits | Check `TARGET_ID` in the selected script and whether matching detections arrive within `LOST_TIMEOUT`. |
| Search never starts | The search follower requires at least one previous detection of the target. |
| Unexpected or conflicting movement | Check `rostopic info /cmd_vel`; stop competing follower or teleoperation nodes. |
| Movement stops intermittently | Inspect detection timing and dropped camera frames; the current timeout is only `0.5 s`. |

## Current scope and possible extensions

This is a reactive visual-following prototype. It currently has no web interface, runtime marker selection, map, SLAM, route planning, obstacle avoidance, or autonomous exploration.

Possible extensions for student projects include ROS parameters for configuration, a web interface for selecting a target ID, controlled exploration before first detection, proportional steering, obstacle-aware navigation, and automated tests for controller decisions and loss/reacquisition behavior. These are proposed extensions, not implemented features.

## Repository preparation and license

Before sharing the project, exclude generated `__pycache__/` and `*.pyc` files and review the duplicate `artag_tracker.launch>` file. The supplied `package.xml` still has a placeholder maintainer and `<license>TODO</license>`; no license file is included. Set the intended maintainer and license before distributing the code under a specific license.
