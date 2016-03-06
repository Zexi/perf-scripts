#!/bin/bash

if [ $(id -u) != 0 ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

script_name=$(basename $0)

[ -n "$HOSTNAME" ] || HOSTNAME=$(hostname)
[ -n "$SRC" ] || export SRC=$(dirname $(dirname $(readlink -e -v $0)))

TMP="/tmp/perf-test"

usage() {
    echo "Usage: $script_name [options] <script>/<jobfile>"
    echo "options: "
    #echo "--hdd partition: HDD partition for IO tests"
    #echo "--ssd partition: SSD partition for IO tests"
    echo "--dry-run: preview changes will made testbox by install"
}

while [ $# -gt 0 ]
do
    case "$1" in
#        --hdd)
#            hdd_partitions=$2
#            shift
#            ;;
#        --ssd)
#            ssd_partitions=$2
#            shift
#            ;;
#        --dry-run)
#            DRY_RUN=0
#            ;;
        *)
            break
            ;;
    esac
    shift
done

make_wakeup() {
    echo "make -C $SRC/monitors/event"
    [ -n "$DRY_RUN" ] && return

    [ -x "$SRC/monitors/event/wakeup" ] || {
        make -C "$SRC/monitors/event" wakeup    
    }
}

create_package_dir() {
    [ -n "$DRY_RUN"] && return

    mkdir -p $TMP
    mkdir -p '/tmp/perf-test/paths'
    mkdir -p '/tmp/perf-test/benchmarks'
}

create_host_config() {
    [ -n "$DRY_RUN"] && return 

    local host_config="$SRC/hosts/${HOSTNAME}"
    [ -e $host_config ] || {
        echo "Creating testbox configuration file: $host_config"

        local mem_kb="$(grep MemTotal /proc/meminfo | awk '{print $2}')"
        local mem_gb="$(((mem_kb)/1024/1024))"

        cat <<"EOF" >> $host_config
memory: ${mem_gb}G
hdd_partitions: ${hdd_partitions}
ssd_partitions: ${ssd_partitions}
EOF
    }
}

parse_yaml() {
    local s='[[:space:]]*'
    local w='[a-zA-Z0-9_]*'
    local tmp_filter="$(mktemp)"
    ls -LR $SRC/setup $SRC/monitors $SRC/tests $SRC/daemon > $tmp_filter
	scripts=$(cat $1 | sed -ne "s|^\($s\):|\1|" \
	         -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\2|p" \
	         -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\2|p" | grep -x -F -f $tmp_filter | grep -v -e ':$' -e '^$')
}

. $SRC/lib/detect-system.sh
. $SRC/lib/install.sh

install_packages() {
    local script=$1
    local distro=$2

    local packages="$(get_dependency_packages ${distro} ${script})"
    local dev_packages="$(get_dependency_packages ${distro} ${script}-dev)"
    packages="$(echo $packages $dev_packages | tr '\n' ' ')"
    [ -n "$packages" -a "$packages" != " " ] || return

    echo "Use: $SRC/distro/installer/$distro install $packages"
    [ -n "$DRY_RUN" ] && return

    $SRC/distro/installer/$distro $packages || {
        echo "Cannont install some packages in $SRC/distro/depends/${script}"
        exit 1
    }
}

build_install_benchmarks() {
    local script=$1
    local distro=$2

    [ -x "$SRC/pack/$script" ] || return

    echo "Making $script benchmark for $distro"
    [ -n "$DRY_RUN" ] && return

    local pkg_name
    pkg_name=$(printf '%s-ps\n' "$script" | sed 's/_/-/g')

    $SRC/sbin/pack -d $distro -c $script
    if [ $? -eq 0 ]; then
        echo "Just make /tmp/perf-test/benchmarks/$script-$(uname -m).cgz" 
#        case $distro in
#            debian|ubuntu)
#                dpkg -i /tmp/$pkg_name.deb ;;
#            fedora|centos)
#                rpm -ivh --replacepkgs /tmp/$pkg_name/RPMS/$pkg_name.$(uname -m).rpm ;;
#            *)
#                echo "Just make /tmp/perf-test/benchmarks/$script-$(uname -m).cgz" ;;
#        esac
    else
        echo "Making $pkg_name failed"
    fi
}

[ $# -eq 0 ] && {
    usage
    exit
}

. $SRC/lib/detect-system.sh
. $SRC/lib/install.sh

detect_system
distro=$_system_name_lowercase

make_wakeup
create_package_dir
create_host_config
install_packages "ps" $distro

for filename in "$@"
do
    scripts=
    if [ -x "$filename" ]; then
        scripts=$(basename $filename)
    elif [ ${filename##*.} = "yaml" ]; then
        if [ -f $filename ]; then
            parse_yaml $filename
        else
            echo "$0: cannot find file $filename" >&2
        fi
    else
        echo "$0: skip unknow parameter $filename" >&2
    fi

    for script in $scripts
    do
        install_packages "$script" $distro
        build_install_benchmarks "$script" $distro
    done
done
