#!/bin/bash
# Export SMART temperature metrics for Prometheus Node Exporter textfile collector.
# When a disk's temperature cannot be read, the metric line is omitted entirely
# so Prometheus can detect the absence via absent() / absent_over_time().

echo "# HELP smart_temperature_celsius Temperature of the drive in Celsius"
echo "# TYPE smart_temperature_celsius gauge"

# List of disks to monitor
disks="/dev/disk0 /dev/disk6 /dev/disk8 /dev/disk10"

for disk in $disks; do
  if [ -e "$disk" ]; then
    # Map device to pretty name
    case $disk in
      "/dev/disk0")  name="INTERNAL" ;;
      "/dev/disk6")  name="KINGSTON" ;;
      "/dev/disk8")  name="TOSHIBA" ;;
      "/dev/disk10") name="MEDIA" ;;
      *)             name="$disk" ;;
    esac

    dev_label=${disk#/dev/}

    # Get temperature
    temp=$(sudo smartctl -a "$disk" | grep -i "Temperature:" | head -n 1 | awk '{print $2}')

    # Fallback for some HDDs
    if [ -z "$temp" ]; then
      temp=$(sudo smartctl -a "$disk" | grep "Temperature_Celsius" | awk '{print $10}')
    fi

    # Omit metric line entirely when temperature cannot be read
    if [ -n "$temp" ]; then
      echo "smart_temperature_celsius{device=\"$dev_label\", name=\"$name\"} $temp"
    else
      echo "[smartmon.sh] WARN: No temperature data for $disk ($name) — omitting metric" >&2
    fi
  fi
done
