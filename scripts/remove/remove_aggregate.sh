#!/bin/sh
#2015.8.30 test ok
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remove_aggregate_run.sh
RUN_LOG=${dir}/remove_aggregate_run.log

az=${1}
az=${az%%".huawei.com"}
. /root/env.sh

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
id_list=`nova aggregate-list | grep ${az} | awk -F"|" '{print $2}'`
for id in `echo ${id_list}`
do
    echo sleep 1s >> ${RUN_SCRIPT}
    echo nova aggregate-remove-host ${id} ${az} >> ${RUN_SCRIPT}
    echo nova aggregate-delete ${id} >> ${RUN_SCRIPT}
done

nova_service_id=`nova service-list | grep ${az} | awk -F "|" '{print $2}'`
echo nova service-disable ${az} nova-compute >> ${RUN_SCRIPT}
echo nova service-delete ${nova_service_id} >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1
