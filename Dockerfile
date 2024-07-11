
FROM osrf/ros:humble-desktop-jammy

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y \
    python3-pip \
    ssh \
    wget \
    nano \
    ros-humble-rmw-cyclonedds-cpp

RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc

WORKDIR /workspace

RUN mkdir -p /workspace/src
COPY ./calibration_tools_standalone_tartan.repos ./
COPY ./find_pkgs.sh ./
COPY ./cyclone_dds.xml ./

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ENV CYCLONEDDS_URI=file:///workspace/cyclone_dds.xml

# Enable ROS log colorised output
ENV RCUTILS_COLORIZED_OUTPUT=1

RUN --mount=type=ssh mkdir -p ~/.ssh \
    && ssh-keyscan github.com >> ~/.ssh/known_hosts \
    && vcs import src < calibration_tools_standalone_tartan.repos

RUN rosdep install -y --from-paths `colcon list --packages-up-to sensor_calibration_tools -p` --ignore-src

RUN source /opt/ros/humble/setup.bash && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --packages-up-to sensor_calibration_tools

RUN rm -rf /var/lib/apt/lists/*

RUN echo "source /workspace/install/setup.bash" >> /etc/bash.bashrc \
    && echo 'alias colcon_build="colcon build --symlink-install \
            --cmake-args -DCMAKE_BUILD_TYPE=Release \
            --packages-up-to sensor_calibration_tools \
            && source install/setup.bash"' >> /etc/bash.bashrc


CMD ["bash"]