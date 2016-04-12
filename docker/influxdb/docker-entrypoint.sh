#!/bin/bash
# vim: set ts=8 sts=4 et tw=72 sw=4:

# set -m

if [ "$1" = 'influxd' -o "$1" = 'supervisor' ]; then

    chown influxdb:influxdb /var/local/influxdb/*



    # Clear unused options

    if [ "${SSL_CERT}" == "**None**" ]; then
        unset SSL_CERT
    fi

    if [ "${SSL_SUPPORT}" == "**False**" ]; then
        unset SSL_SUPPORT
    fi

    # Modify config with environment variables
    echo "Checking environment variables for config overrides..."
    /usr/local/sbin/env-ini.py < ${INFLUX_CONFIG}.orig > ${INFLUX_CONFIG}
    cat ${INFLUX_CONFIG}

    # After our initial config, but before (possibly) bootstrapping auth,
    # run any other prestart init scripts

    if [ -d /usr/local/etc/docker-influxdb/prestart-init.d ]; then
        for f in /usr/local/etc/docker-influxdb/prestart-init.d/*.sh; do
            [ -f "$f" ] && . "$f"
        done
    fi

    # Before activating authentication we need to run up the server and create a user.

    if [ -n "${INFLUX_PASSWORD}" -a -n "${INFLUX_ADMIN_USER}" ]; then
        if grep 'auth-enabled = true' ${INFLUX_CONFIG} >/dev/null ; then
            echo "InfluxDB authentication already activated"
        else
            echo "About to bootstrap InfluxDB authentication with user: ${INFLUX_ADMIN_USER}"
            gosu influxdb /usr/bin/influxdb/influxd -config=${INFLUX_CONFIG} &
            bgPID=$!
    
            #wait for the startup of influxdb
            echo "InfluxDB started with PID ${bgPID}, wait for database."
            false
            until [ $? == 0 ] ; do
                sleep 1
                /usr/bin/influxdb/influx -execute "SHOW USERS" >/dev/null 2>&1
            done
            echo "Database ready, adding user"
            gosu influxdb /usr/bin/influxdb/influx -execute "CREATE USER ${INFLUX_ADMIN_USER} WITH PASSWORD '${INFLUX_ADMIN_PASS}' WITH ALL PRIVILEGES"
            
            gosu influxdb /usr/bin/influxdb/influx -execute "SHOW USERS"

            echo "Enabling authgentication"
            sed -i 's/auth-enabled = false/auth-enabled = true/' ${INFLUX_CONFIG}

            # Now bring back the server and terminate it
            echo "Bootstrap complete, restarting with authentication active"
            kill ${bgPID}
        fi
    fi



    ls -ld /var/local/influxdb/*
    echo "Starting InfluxDB ..."

    if [ "$1" = 'supervisor' ]; then
        exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
    else
        exec gosu influxdb "$@"
    fi
fi

exec "$@"
