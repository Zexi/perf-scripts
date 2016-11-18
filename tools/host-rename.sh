#!/bin/bash

usage() {
    echo "Usage: $(basename $0) <new-hostname>"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
else
    new_hostname="$1"
fi

echo $new_hostname > /etc/hostname
hostname $new_hostname
hostnamectl set-hostname $new_hostname
