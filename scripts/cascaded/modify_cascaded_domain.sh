#!/bin/sh
dir=`cd "$(dirname "$0")"; pwd`
RUN_SCRIPT=${dir}/modify_cascaded_domain_run.sh
LOG=${dir}/modify_cascaded_domain_run.log

cascading_domain=${1}
cascaded_domain=${2}

ifs=$IFS
IFS='.' arr=(${cascaded_domain})
IFS=$ifs

cascaded_localaz=${arr[0]}
cascaded_localdz=${arr[1]}
cascaded_region=${cascaded_localaz}"."${cascaded_localdz}

domainpostfix=${cascaded_domain#$cascaded_region"."}

which_sh=`which sh`
echo "#!"${which_sh} > ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-agent-central\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-agent-central >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-agent-central >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service ceilometer ceilometer-agent-central >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-agent-compute\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-agent-compute >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-agent-compute >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service ceilometer ceilometer-agent-compute >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-agent-notification\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-agent-notification >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-agent-notification >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service ceilometer ceilometer-agent-notification >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-agent-hardware\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-agent-hardware >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-agent-hardware >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-alarm-evaluator\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-alarm-evaluator >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-alarm-evaluator >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service ceilometer ceilometer-alarm-evaluator >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-alarm-fault\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-alarm-fault >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-alarm-fault >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service ceilometer ceilometer-alarm-fault >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-alarm-notifier\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-alarm-notifier >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-alarm-notifier >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-api\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-api >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ceilometer ceilometer-collector\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ceilometer ceilometer-collector >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ceilometer ceilometer-collector >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cinder cinder-api\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service cinder cinder-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter storage_availability_zone=${cascaded_region} --service cinder cinder-api >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cinder cinder-backup\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-backup >> ${RUN_SCRIPT}
echo cps template-params-update --parameter storage_availability_zone=${cascaded_region} --service cinder cinder-backup >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cinder cinder-scheduler\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-scheduler >> ${RUN_SCRIPT}
echo cps template-params-update --parameter storage_availability_zone=${cascaded_region} --service cinder cinder-scheduler >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cinder cinder-volume\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-volume >> ${RUN_SCRIPT}
echo cps template-params-update --parameter storage_availability_zone=${cascaded_region} --service cinder cinder-volume >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"collect info-collect-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service collect info-collect-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service collect info-collect-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"collect info-collect-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service collect info-collect-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service collect info-collect-client >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cps cps-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service cps cps-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service cps cps-client >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cps cps-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service cps cps-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service cps cps-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cps network-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service cps network-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service cps network-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service cps network-client >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cps network-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service cps network-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service cps network-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service cps network-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"cps cps-web\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_domain=https://image.${cascading_domain}:443 --service cps cps-web >> ${RUN_SCRIPT}
echo cps template-params-update --parameter keystone_domain=https://identity.${cascading_domain}:443 --service cps cps-web >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service cps cps-web >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service cps cps-web >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"gaussdb gaussdb\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service gaussdb gaussdb >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"glance glance\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter api_auth_host=identity.${cascading_domain} --service glance glance >> ${RUN_SCRIPT}
echo cps template-params-update --parameter registry_auth_host=identity.${cascading_domain} --service glance glance >> ${RUN_SCRIPT}
echo cps template-params-update --parameter swift_store_auth_address=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service glance glance >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"haproxy haproxy\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter localurl=${cascaded_domain} --service haproxy haproxy >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"heat heat\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service heat heat >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_uri=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service heat heat >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"log log-agent\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service log log-agent >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service log log-agent >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"log log-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service log log-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service log log-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"mongodb mongodb\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service mongodb mongodb >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"neutron neutron-reschedule\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service neutron neutron-reschedule >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"neutron neutron-metadata-agent\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service neutron neutron-metadata-agent >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service neutron neutron-metadata-agent >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"neutron neutron-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service neutron neutron-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter nova_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service neutron neutron-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-api\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service nova nova-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter default_availability_zone=${cascaded_region} --service nova nova-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter keystone_ec2_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-api >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-compute\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter default_availability_zone=${cascaded_region} --service nova nova-compute >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-compute >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-compute >> ${RUN_SCRIPT}
echo cps template-params-update --parameter novncproxy_base_url=https://nova-novncproxy.${cascaded_domain}:8002/vnc_auto.html --service nova nova-compute >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-conductor\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-conductor >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-conductor >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-novncproxy\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-novncproxy >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-novncproxy >> ${RUN_SCRIPT}
echo cps template-params-update --parameter novncproxy_base_url=https://nova-novncproxy.${cascaded_domain}:8002/vnc_auto.html --service nova nova-novncproxy >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-scheduler\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-scheduler >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-scheduler >> ${RUN_SCRIPT}
echo cps template-params-update --parameter default_availability_zone=${cascaded_region} --service nova nova-scheduler >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ntp ntp-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ntp ntp-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ntp ntp-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ntp ntp-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ntp ntp-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ntp ntp-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"swift swift-proxy\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service swift swift-proxy >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"upg upg-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service upg upg-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service upg upg-client >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"upg upg-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service upg upg-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service upg upg-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"backup backup-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service backup backup-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service backup backup-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"backup backup-client\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service backup backup-client >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_region_name=${cascaded_region} --service backup backup-client >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"fusionnetwork oam-network-server\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service fusionnetwork oam-network-server >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service fusionnetwork oam-network-server >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"nova nova-compute-ironic\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-compute-ironic >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service nova nova-compute-ironic >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ironic ironic-api\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ironic ironic-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service ironic ironic-api >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ironic ironic-api >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ironic ironic-conductor\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter auth_host=identity.${cascading_domain} --service ironic ironic-conductor >> ${RUN_SCRIPT}
echo cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service ironic ironic-conductor >> ${RUN_SCRIPT}
echo cps template-params-update --parameter os_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ironic ironic-conductor >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

echo "echo \"ironic ironicproxy\"" >> ${RUN_SCRIPT}
echo cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service ironic ironicproxy >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

ip=`ip addr show brcps | grep "secondary brcps:cps-s" | awk '{print $2}' | awk -F '[/]' '{print $1}'`
echo curl -k -X POST -H '"'Content-Type: application/json'"' https://${ip}:8000/cps/v1/haproxylocalurl -d "'"{'"'localdc'"': '"'${cascaded_localdz}'"', '"'localaz'"': '"'${cascaded_localaz}'"', '"'localurl'"':'"'${cascaded_domain}'"', '"'domainpostfix'"': '"'${domainpostfix}'"'}"'" >> ${RUN_SCRIPT}
echo cps commit  >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1

temp=`cat ${LOG} | grep refused`
if [ -n "${temp}" ]; then
    exit 127
fi
exit 0
