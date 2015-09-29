#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/add_cinder_type_run.sh
LOG=${dir}/add_cinder_type_run.log

az_domain=${1}
az_region=${az_domain%%".huawei.com"}
. /root/env.sh

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}
echo ". /root/env.sh" >> ${RUN_SCRIPT}

echo cinder type-create magnetic@${az_region} >> ${RUN_SCRIPT}
echo cinder type-key magnetic@${az_region} set volume_backend_name=AMAZONEC2 >> ${RUN_SCRIPT}

echo cinder type-create hybrid@${az_region}  >> ${RUN_SCRIPT}
echo cinder type-key hybrid@${az_region} set volume_backend_name=HYBRID:${az_region}:az01.shenzhen--fusionsphere >> ${RUN_SCRIPT}

echo cps host-template-instance-operate --action stop --service cinder cinder-volume >> ${RUN_SCRIPT}
echo sleep 1s >> ${RUN_SCRIPT}
echo cps host-template-instance-operate --action start --service cinder cinder-volume >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1
