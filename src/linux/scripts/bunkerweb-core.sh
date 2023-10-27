#!/bin/bash

# Source the utils script
# shellcheck disable=SC1091
source /usr/share/bunkerweb/helpers/utils.sh
# shellcheck disable=SC1091
source /usr/share/bunkerweb/scripts/utils.sh

export PYTHONPATH=/usr/share/bunkerweb/deps/python

# Create the core.conf file if it doesn't exist
if [ ! -f /etc/bunkerweb/core.conf ]; then
    cp /usr/share/bunkerweb/core/core.conf.example /etc/bunkerweb/core.conf
fi

# Function to start the Core
function start() {
    log "SYSTEMCTL" "ℹ️" "Starting Core"
    output="$(python3 /usr/share/bunkerweb/core/app/core.py 2>&1)"
    ret=$?

	if [ $ret == 1 ] ; then
        # Show the output of the core
		log "ENTRYPOINT" "❌ " "$output"
		exit 1
	elif [ $ret == 2 ] ; then
		log "ENTRYPOINT" "❌ " "Invalid LISTEN_PORT, It must be an integer between 1 and 65535."
		exit 1
	elif [ $ret == 3 ] ; then
		log "ENTRYPOINT" "❌ " "Invalid MAX_WORKERS, It must be a positive integer."
		exit 1
	elif [ $ret == 4 ] ; then
		log "ENTRYPOINT" "❌ " "Invalid MAX_THREADS, It must be a positive integer."
		exit 1
	fi

    # shellcheck disable=SC1091
	source /tmp/core.tmp.env
	rm -f /tmp/core.tmp.env

    python3 -m gunicorn --chdir /usr/share/bunkerweb/core \
        --pythonpath /usr/share/bunkerweb/deps/python/ \
        --config /usr/share/bunkerweb/core/gunicorn.conf.py \
        --user nginx \
        --group nginx \
        --bind "127.0.0.1":"$LISTEN_PORT" &
    echo $! > /var/run/bunkerweb/core.pid
}

# Check the command line argument
case $1 in
    "start")
        start
        exit $?
        ;;
    "stop")
        stop "core"
        exit $?
        ;;
    "reload")
        stop "core"
        # shellcheck disable=SC2181
        if [ $? -ne 0 ] ; then
            exit 1
        fi
        sleep 5
        start
        exit $?
        ;;
    *)
        echo "Invalid option!"
        echo "List of options availables:"
        display_help "core"
        exit 1
esac
