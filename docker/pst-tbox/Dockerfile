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

# Install sysbench and configure mysql
# Install MySQL Server in a Non-Interactive mode. Default root password will be "pass"
RUN echo "mysql-server-5.6 mysql-server/root_password password pass" | debconf-set-selections && \
    echo "mysql-server-5.6 mysql-server/root_password_again password pass" | debconf-set-selections && \
    apt-get -y install mysql-server-5.6 && \
    service mysql start && mysql -u root -ppass -e "create database test"

# Install and run benchmarks
ENV TBOX_JOBS ${TBOX_JOBS:-superpi;ping;sysbench}
ADD ./run.py /run.py

ENTRYPOINT ["/run.py"]
