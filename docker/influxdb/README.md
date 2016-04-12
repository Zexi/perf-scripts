# VRT Systems Docker InfluxDB
## VERSION               0.2.0

Docker image to run InfluxDB in a container.

Derived from [tutumcloud/tutum-docker-influxdb](https://github.com/tutumcloud/tutum-docker-influxdb).

Uses VRT's default /var/local for storing data.


## Usage

To create the image `vrtsystems/influxdb`, execute the following command on docker-influxdb folder:

    docker build -t vrtsystems/influxdb .

### Deployment

Start your image binding the external ports `8083` and `8086` in all interfaces to your container. Ports `8090` and `8099` are only used for clustering and should not be exposed to the internet.

    docker run -d -p 8083:8083 -p 8086:8086 --expose 8090 --expose 8099 vrtsystems/influxdb

### Environment Variables

The default install for InfluxDB (since 0.9) begins with authentication
disabled, and it is the responsibility of the installer to set an admin
account and activate authentication. This image makes that easy through
support for the following environment variables:

* `INFLUX_ADMIN_PASS` - sets the superuser password for InfluxDB. The
  default superuser is defined by the `INFLUX_ADMIN_USER` environment variable.

* `INFLUX_ADMIN_USER` - used in conjunction with `INFLUX_ADMIN_PASS` to set a
  user and its password. This variable will create the specified user with
  admin privileges. If it is not specified, then the default user of `root`
  will be used.

If these are not supplied, the database will be left in its default
 (**UNSECURED**) state. Please provide these variables. 

In addition to the explict support for admin user creation, the container
entrypoint also checks for environment variables to override settings in
the config file. These are of the form `IX_[section]_[setting]` where
hyphens in the section or setting are converted to underscores. The global
`reporting-disabled` setting near the top of the file can be set with
`IX__REPORTING_DISABLED`, and settings in (for example) a section as follows:

    [meta]
    dir = "/var/local/influxdb/meta"
    hostname = "localhost"
    bind-address = ":8088"

... the settings could be modified by setting environment variables
`IX_META_DIR`, `IX_META_HOSTNAME` and `IX_META_BIND_ADDRESS`. Note that Influx
is particular about quotes, so if you want to set a string value, you'll need
to pass those in explicitly (note the extra `'` below). In a Dockerfile:

    ENV IX_META_HOSTNAME '"myhostname"'

or on the command line:

    docker run -e 'IX_META_HOSTNAME="myhostname"'

## How to extend this image

### With a Dockerfile

You can extend the image with a `Dockerfile` to add features or customise its behaviour for a specific application (e.g. see prestart-init.d and poststart-init.d) below.

### With a shell script in prestart-init.d

If you would like to perform initialization before the database is started, you
can add a `*.sh` script under `/usr/local/etc/docker-influxdb/prestart-init.d/`.
The entry point will source any `*.sh` script found in that directory before
starting the service. If you need to execute commands against a running
database, use poststart-init.d.

### With a shell script in poststart-init.d

In addition to the prestart hook above, this image provides an init capability
specifically for running scripts against the database server. Add `*.sh` scripts
under `/usr/local/etc/docker-influxdb/poststart-init.d/` and once the database
is started these will be sourced and run with the influxdb system user. Note
that you can access `INFLUX_ADMIN_USER` and `INFLUX_ADMIN_PASS` in these scripts to
authenticate against the database, for example:

    #!/bin/bash
    influx -username "${INFLUX_ADMIN_USER}" -password "${INFLUX_ADMIN_PASS}" \
        -execute "CREATE DATABASE mydb1"
    influx -username "${INFLUX_ADMIN_USER}" -password "${INFLUX_ADMIN_PASS}" \
        -execute "CREATE USER myuser1 WITH PASSWORD '${SOME_PASS}'"
    influx -username "${INFLUX_ADMIN_USER}" -password "${INFLUX_ADMIN_PASS}" \
        -execute "GRANT WRITE ON mydb1 TO myuser1"
    influx -username "${INFLUX_ADMIN_USER}" -password "${INFLUX_ADMIN_PASS}" \
        -execute "CREATE RETENTION POLICY mypolicy1 ON mydb1 DURATION 1d REPLICATION 1 DEFAULT"

## History

See [CHANGELOG.md](CHANGELOG.md)

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 
