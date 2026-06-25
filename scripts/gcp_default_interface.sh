#!/bin/bash
# Detects the default network interface used for external traffic.
# Useful for identifying the correct device label for GCP egress monitoring.
# Usage: ./scripts/gcp_default_interface.sh

default_if=$(route -n get default 2>/dev/null | grep "interface:" | awk '{print $2}')
if [ -n "$default_if" ]; then
    echo "Default interface: $default_if"
else
    echo "Could not detect default interface" >&2
    exit 1
fi
