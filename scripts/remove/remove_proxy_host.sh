#!/bin/sh
#2015.8.18 test ok
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/remote_proxy_host_run.sh
RUN_LOG=${dir}/remote_proxy_host_run.LOG

id=${1}

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
role_list=`cps host-list | awk -F "|" -v d=${id} 'begin{flag=0}{if(flag==0 && $2~d){flag=1;print $4}else if(flag==1 && !($2~/-/)){print $4}else{flag=0}}'`
for role in `echo ${role_list}`
do
    echo cps role-host-delete --host ${id} ${role//","/""} >> ${RUN_SCRIPT}
done

#echo cps host-delete --host ${id} >> ${RUN_SCRIPT}
echo cps commit >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${RUN_LOG} 2>&1

