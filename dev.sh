#!/bin/bash
# ----------------------------------------------------------------
# Build docker dev stage and add local code for live development
# ----------------------------------------------------------------

# Default value for headless
headless=false

# Function to print usage
usage() {
    echo "Usage: dev.sh [--headless] [--help | -h]"
    echo ""
    echo "Options:"
    echo "  --headless     Run the Docker image without X11 forwarding"
    echo "  --help, -h     Display this help message and exit."
    echo ""
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




MOUNT_X=""
if [ "$headless" = "false" ]; then
    MOUNT_X="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix"
    xhost + >/dev/null
fi

# Get the absolute path of the script
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# Run docker image with local code volumes for development
docker run -it --rm --net host --privileged \
    ${MOUNT_X} \
    -e XAUTHORITY="${XAUTHORITY}" \
    -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    -v /dev:/dev \
    -v /tmp:/tmp \
    -v /etc/localtime:/etc/localtime:ro \
    -v ./cyclone_dds.xml:/workspace/cyclone_dds.xml \
    -v ./find_pkgs.sh:/workspace/find_pkgs.sh \
    -v ./calibrators:/workspace/src/calibration_tools/calibrators \
    calibration_tools:latest-dev 
