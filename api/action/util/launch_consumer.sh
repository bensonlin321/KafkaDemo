#!/bin/bash
SCRIPT="consumer.py"

# check consumer count
MAX=2
ROOT="$( cd "$(dirname "$0")" ; pwd -P )"

SCRIPT_PATH=$ROOT/$SCRIPT;
for sitenu in $(seq 1 $MAX)
do
    RUNNING=`ps aux | grep "$SCRIPT $sitenu" | grep -v grep`
    if [ -z "$RUNNING" ]; then
        echo "nohup python3 $SCRIPT_PATH $sitenu > /tmp/consumer$sitenu.out 2> /tmp/consumer$sitenu.err &"
        nohup python3 $SCRIPT_PATH $sitenu > /tmp/consumer$sitenu.out 2> /tmp/consumer$sitenu.err &
        sleep 1
    fi
done
