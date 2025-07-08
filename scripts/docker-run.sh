#!/bin/bash

# Set user and group IDs to match host user
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

echo "Using USER_ID=$USER_ID and GROUP_ID=$GROUP_ID"

# Run docker-compose with the correct user permissions
docker-compose "$@" 