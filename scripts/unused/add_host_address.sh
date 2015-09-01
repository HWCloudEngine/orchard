#!/usr/bin/sh
#2015.8.18 test ok
address=${1}
cps template-params-update --parameter address=${address} --service dns dns-server
cps commit 