#!/bin/sh
temp=`cps host-list | awk -F "|" '{if (!($4~/[a-z]/) && ($2~/[A-Z]/)) print $2 $4}'`
result=""
for id in `echo ${temp}`
do
    if [ "${result}" != "" ]; then
	    result=${result}","
	fi
	result=${result}${id}
done

echo ${result}