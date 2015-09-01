#!/bin/sh
#2015.8.18 test ok
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remove_keystone_endpoint_run.sh
RUN_LOG=${dir}/remove_keystone_endpoint_run.LOG

az=${1}
az=${az%%".huawei.com"}
. /root/env.sh

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}
echo "id_list=\`keystone endpoint-list | grep "${az}" | awk -F \"|\" '{print \$2}'\`" >> ${RUN_SCRIPT}
echo "for id in \`echo \${id_list}\`" >> ${RUN_SCRIPT}
echo "do" >> ${RUN_SCRIPT}
echo "   keystone endpoint-delete \$id" >> ${RUN_SCRIPT}
echo "done" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

