#!/bin/bash
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/add_route_run.sh
RUN_LOG=${dir}/add_route_run.log

subnet=${1}
gw=${2}

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
echo "ip route show | grep ${subnet} && ip route del ${subnet}" >> ${RUN_SCRIPT}
echo "ip route add ${subnet} via ${gw}" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1