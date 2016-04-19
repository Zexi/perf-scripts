# Pull base image
FROM ubuntu:14.04
MAINTAINER Zexi Li <zexi.li@aliyun.com>

RUN sed -i 's|\(http://\).*\(/ubuntu/\)|\1mirrors.aliyun.com\2|g' /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y rrdtool mongodb python python-yaml python-rrdtool python-pymongo python-tornado python-pip git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade influxdb

RUN git clone -b dev https://github.com/Zexi/perf-scripts/
WORKDIR /perf-scripts/docker/pst-server

# Post Port
EXPOSE 8080

ADD ./run.py /run.py
ENTRYPOINT ["/run.py"]
