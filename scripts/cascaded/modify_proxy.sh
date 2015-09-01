#!/usr/bin/sh
#2015.8.18 test ok
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/modify_proxy_run.sh
LOG=${dir}/modify_proxy_run.log

api_ip=${1}
gateway=${2}

haproxy_external_api_ip='[{"backendservice": "all", "frontendport": "443", "systeminterface": "external_api", "mask": "24", "frontendip": "'${api_ip}'", "gateway": "'${gateway}'"}]'
haproxy_frontssl='[{"certfile": "", "ssl": "true", "backendservice": "all", "frontendport": "443", "keyfile": "", "frontendip": "'${api_ip}'"}]'

apacheproxy_external_api_ip='[{"systeminterface": "external_api", "mask": "24", "gateway": "'${gateway}'", "ip": "'${api_ip}'"}]'       
apacheproxy_proxy_remote_match='[{"regex": ".*", "ProxySourceAddress": "'${api_ip}'", "vhost_port": 8081}]'

network_str="'"'[{"ip": "'${api_ip}'", "systeminterface": "external_api", "mask": "24", "gateway": "'${gateway}'"}]'"'"

echo "#!/usr/bin/sh" > ${RUN_SCRIPT}
echo cps template-params-update --parameter external_api_ip="'"${haproxy_external_api_ip}"'" --service haproxy haproxy >> ${RUN_SCRIPT}
echo cps template-params-update --parameter frontssl="'"${haproxy_frontssl}"'" --service haproxy haproxy >> ${RUN_SCRIPT}

echo cps template-params-update --parameter external_api_ip="'"${apacheproxy_external_api_ip}"'" --service apacheproxy apacheproxy >> ${RUN_SCRIPT}
echo cps template-params-update --parameter proxy_remote_match="'"${apacheproxy_proxy_remote_match}"'" --service apacheproxy apacheproxy >> ${RUN_SCRIPT}

echo cps template-params-update --parameter network=${network_str} --service dns dns-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter default_gateway=${gateway} --service cps network-client >> ${RUN_SCRIPT}

echo cps commit >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1

temp=`cat ${LOG} | grep refused`
if [ -n "${temp}" ]; then
    exit 127
fi
exit 0
