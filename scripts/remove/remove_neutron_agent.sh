#!/bin/sh
#2015.8.30 test ok
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remote_neutron_agent_run.sh
RUN_LOG=${dir}/remote_neutron_agent_run.log

az_domain=${1}
az_hostname=${az_domain%%".huawei.com"}

. /root/env.sh

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}
echo ". /root/env.sh" >> ${RUN_SCRIPT}

agent_id_list=`neutron agent-list | grep ${az_hostname} | awk -F "|" '{print $2}'`

for agent_id in `echo ${agent_id_list}`
do
    echo neutron agent-delete ${agent_id} >> ${RUN_SCRIPT}
done

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
