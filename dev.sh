#!/bin/bash
# ----------------------------------------------------------------
# Build docker dev stage and add local code for live development
# ----------------------------------------------------------------


# Default cyclone_dds.xml path
CYCLONE_DIR=/home/$USER/cyclone_dds.xml
CYCLONE_VOL="-v $CYCLONE_DIR:/workspace/cyclone_dds.xml"

# Default value for headless
headless=false

# Function to print usage
usage() {
    echo "
Usage: dev.sh [--headless] [--help | -h]

Options:
  --headless     Run the Docker image without X11 forwarding
  --help, -h     Display this help message and exit."
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --headless) headless=true ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
    shift
done

# Verify CYCLONE_DIR exists
if [ -n "$CYCLONE_VOL" ]; then
    if [ ! -f "$CYCLONE_DIR" ]; then
        echo "$CYCLONE_DIR does not exist! This scirpt requires a cyclone_dds.xml file in HOME dir"
        exit 1
    fi
fi

MOUNT_X=""
if [ "$headless" = "false" ]; then
    MOUNT_X="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix"
    xhost + >/dev/null
fi

# Get the absolute path of the script
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

mkdir -p $SCRIPT_DIR/calib_data

# Run docker image with local code volumes for development
docker run -it --rm --net host --privileged \
    --gpus all \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    ${MOUNT_X} \
    -e XAUTHORITY="${XAUTHORITY}" \
    -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    -v /dev:/dev \
    -v /tmp:/tmp \
    -v /etc/localtime:/etc/localtime:ro \
    -v ./calibrators:/workspace/src/calibrators \
    -v ./common:/workspace/src/common \
    -v ./sensor_calibration_tools:/workspace/src/sensor_calibration_tools \
    -v ./system:/workspace/src/system \
    -v ./calib_data:/workspace/calib_data \
    $CYCLONE_VOL \
    calibration_tools:latest-dev
