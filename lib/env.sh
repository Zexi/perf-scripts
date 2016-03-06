#!/bin/sh

has_cmd()
{
	command -v "$1" >/dev/null
}

nproc()
{
	if has_cmd 'nproc'; then
		command 'nproc'
	elif has_cmd 'getconf'; then
		getconf '_NPROCESSORS_CONF'
	else
		grep -c '^processor' /proc/cpuinfo
	fi
}

is_virt()
{
	if has_cmd 'virt-what'; then
		[ "$(virt-what)" = "kvm" ]
	else
		grep -q -w hypervisor /proc/cpuinfo
	fi
}
