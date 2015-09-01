#!/usr/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/add_dns_run.sh
RUN_LOG=${dir}/add_dns_run.LOG

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
dns_list=`cps template-params-show --service dns dns-server | awk -F "|" 'begin{flag=0}{if(flag==0 && $2~"address"){flag=1;print $3}else if(flag==1 && !($2~"network")){print $3}else{flag=0}}'`
str=""
for line in `echo ${dns_list}`
do
        str=${str}${line}
done

if [ "$1" == "add" ]; then
    echo "hello"
    str=${str}","${2}
elif [ "$1" == "remove" ]; then
    echo "fuck"
    str=${str//${2}/""}
    str=
fi


echo ${str}
#str=${str}${1}
#echo ${str}
echo "#!/usr/bin/sh" > ${RUN_SCRIPT}

echo cps template-params-update --parameter address=${str} --service dns dns-server >> ${RUN_SCRIPT}
echo cps commit >> ${RUN_SCRIPT}

#sh ${RUN_SCRIPT} > ${RUN_LOG}

#rm ${RUN_SCRIPT}
