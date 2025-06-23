#!/bin/bash

# Check for user input
if [ -z "$1" ]; then
	echo "Usage: $0 <number_of_obus>"
	exit 1
fi

OBU_COUNT=$1

# 1. clean old logs
echo "Cleaning old logs..."
rm -f logs/obu_*.log

# 2. ensure logs directory exists
mkdir -p logs

# 3. launch OBUs in background
for i in $(seq 0 $OBU_COUNT); do
	echo "launching OBU $i..."
	nohup python3 OBUs.py --pc_topic_id $i > logs/obu_$i.log 2>&1 &
done

echo "All OBUs launched in background"
