#!/bin/bash

DOCKER_BUILDKIT=1 docker build --ssh default="$SSH_AUTH_SOCK" \
    -t calibration_tools:latest-dev -f Dockerfile .