#!/bin/bash
_influxdb_version=$1
_influxdb_tag=$2
_release_build=false

if [ -z "${_influxdb_version}" ]; then
	source INFLUXDB_VERSION
	_influxdb_version=$INFLUXDB_VERSION
	_influxdb_tag=$INFLUXDB_VERSION
	_release_build=true
fi

echo "INFLUXDB_VERSION: ${_influxdb_version}"
echo "DOCKER TAG: ${_influxdb_tag}"
echo "RELEASE BUILD: ${_release_build}"

docker build --build-arg INFLUXDB_VERSION=${_influxdb_version} --tag "zexi/influxdb:${_influxdb_tag}"  --no-cache=true .

if [ $_release_build == true ]; then
	docker build --build-arg INFLUXDB_VERSION=${_influxdb_version} --tag "zexi/influxdb:latest"  --no-cache=true .
fi
