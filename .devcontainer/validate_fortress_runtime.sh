#!/usr/bin/env bash
# Verify the non-interactive runtime contract required by the simulation launches.
set -eo pipefail

if [[ -n "${ROS_DISTRO:-}" && -r "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
    # shellcheck disable=SC1090
    source "/opt/ros/${ROS_DISTRO}/setup.bash"
elif [[ -r /opt/ros/humble/setup.bash ]]; then
    # shellcheck disable=SC1091
    source /opt/ros/humble/setup.bash
else
    echo 'ROS 2 setup.bash was not found; expected ROS 2 Humble.' >&2
    exit 1
fi

set -u

ign_version="$(ign gazebo --version)"
if ! grep -Eq 'Gazebo[^0-9]*6(\.|$)' <<<"${ign_version}"; then
    echo "Expected Gazebo Fortress (Gazebo Sim 6), got: ${ign_version}" >&2
    exit 1
fi

for ros_package in ros_gz_sim ros_gz_bridge; do
    ros2 pkg prefix "${ros_package}" >/dev/null
done

for system_plugin in \
    'libignition-gazebo6-diff-drive-system.so*' \
    'libignition-gazebo6-sensors-system.so*'; do
    if ! find /usr/lib -type f -name "${system_plugin}" -print -quit | grep -q .; then
        echo "Gazebo Fortress system plugin is not installed: ${system_plugin}" >&2
        exit 1
    fi
done

echo "Gazebo Fortress runtime verified: ${ign_version}"
