#!/bin/sh

if [ -f "/home/user/dont-watch" ]; then
    exit 0
fi

# Check if process alive
TICK_TIME=`stat -c %Y /tmp/bot/bot-daemon.tick`
CURR_TIME=`date +%s`
# If process is not alive
if [ $((CURR_TIME - TICK_TIME)) -ge 300 ]; then
    # Kill it just in case
    kill -9 `cat /tmp/bot/bot-daemon.pid` 2>/dev/null
    # Start
    if [ "`hostname`" = "dell-desktop" ]; then
        cd /home/alevtina/Data/\!Business/Bot/rzd_bot/bot
    else
        cd /usr/local/bot
    fi
    python bot-daemon.py &
    echo `date` "Daemon restarted"
fi