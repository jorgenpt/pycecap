#!/bin/bash

for log in logs/*.log; do
    ./replay.py > /dev/null < $log
    if [ $? -gt 0 ]; then
        echo "Failed on log: $log"
        exit 1
    fi
done
