# Pull base image
FROM ubuntu
MAINTAINER Zexi Li "zexi.li@aliyun.com"

# Change mirror
RUN sed -i 's|\(http://\).*\(/ubuntu/\)|\1mirrors.163.com\2|g' /etc/apt/sources.list

# Install python and pip
RUN \
  apt-get update && \
  apt-get install -y python python-yaml

# Add local perf-scripts to image
ADD . /perf-scripts
WORKDIR /perf-scripts

# Install benchmarks
RUN \
  bin/auto-install.py && \
  rm -rf /var/lib/apt/lists/*
