#!/bin/bash
# NOTE: this script should be run by supervisord as the influxdb user

echo "Starting postinit, wait for database."
false
until [ $? == 0 ] ; do
    sleep 1
    curl localhost:8086/ping >/dev/null 2>&1
done
echo "Database ready, postinit checking for scripts in /usr/local/etc/docker-influxdb/poststart-init.d/"

if [ -d /usr/local/etc/docker-influxdb/poststart-init.d/ ] ; then
    for f in /usr/local/etc/docker-influxdb/poststart-init.d/*.sh ; do
        if [ -f "$f" ] ; then
            echo "Running $f"
            . "$f"
        fi
    done
fi
exit 0
