# Pull base image
FROM ubuntu:14.04
MAINTAINER Zexi Li <zexi.li@aliyun.com>

# Change mirror
RUN sed -i 's|\(http://\).*\(/ubuntu/\)|\1mirrors.aliyun.com\2|g' /etc/apt/sources.list

# Install python and pip
RUN apt-get update && \
    apt-get install -y python python-yaml python-pip git

RUN pip install pytz

# Add perf-scripts to image
RUN git clone -b dev https://github.com/Zexi/perf-scripts/

# Install and run benchmarks
ARG TBOX_JOBS
ENV TBOX_JOBS ${TBOX_JOBS:-superpi;ping}
ADD ./init.py /init.py
RUN /init.py && \
    /perf-scripts/bin/auto-install.py && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/perf-scripts/bin/auto-run.py"]
