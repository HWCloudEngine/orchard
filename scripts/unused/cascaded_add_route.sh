#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/cascaded_add_route_run.sh
LOG=${dir}/cascaded_add_route_run.log

openstack_api_subnet=${1}
aws_api_gw=${2}
openstack_tunnel_subnet=${3}
aws_tunnel_gw=${4}

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}

echo "ip route show | grep ${openstack_api_subnet} && ip route del ${openstack_api_subnet}" >> ${RUN_SCRIPT}
echo "ip route show | grep ${openstack_tunnel_subnet} && ip route del ${openstack_tunnel_subnet}" >> ${RUN_SCRIPT}

echo "ip route add ${openstack_api_subnet} via ${aws_api_gw}" >> ${RUN_SCRIPT}
echo "ip route add ${openstack_tunnel_subnet} via ${aws_tunnel_gw}" >> ${RUN_SCRIPT}

echo "ip route show table external_api | grep ${openstack_api_subnet} && ip route del table external_api ${openstack_api_subnet}" >> ${RUN_SCRIPT}
echo "ip route add table external_api ${openstack_api_subnet} via ${aws_api_gw}" >> ${RUN_SCRIPT}

tunnel_ip=`ifconfig eth3| grep "inet addr"| awk '{print $2}'| awk -F ":" '{print $2}'`
echo "ip rule add from ${tunnel_ip} table 27149" >> ${RUN_SCRIPT}
echo "ip route add default via ${aws_tunnel_gw} table 27149" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1
