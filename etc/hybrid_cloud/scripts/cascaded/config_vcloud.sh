#!/bin/sh
if [ $# != 7 ]; then
    echo "Usage: sh $0 vcloud_host_ip vcloud_org vcloud_vdc vcloud_host_username vcloud_host_password vcloud_tunnel_cidr vcloud_route_gw"
    exit 1
fi


NOVA_CONFIG_FILE=/etc/nova/others/cfg_template/nova-compute.json
CINDER_CONFIG_FILE=/etc/cinder/others/cfg_template/cinder-volume.json

NOVA_CONFIG_FILE_TMP=/etc/nova/others/cfg_template/nova-compute.json.template
CINDER_CONFIG_FILE_TMP=/etc/cinder/others/cfg_template/cinder-volume.json.template




vcloud_host_ip=$1
vcloud_org=$2
vcloud_vdc=$3
vcloud_host_username=$4
vcloud_host_password=$5
vcloud_tunnel_cidr=$6
vcloud_route_gw=$7


echo "config nova..."

sed -i "s/%vcloud_host_ip%/${vcloud_host_ip}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_org%/${vcloud_org}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_vdc%/${vcloud_vdc}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_host_username%/${vcloud_host_username}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_host_password%/${vcloud_host_password}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_tunnel_cidr%/${vcloud_tunnel_cidr}/" ${NOVA_CONFIG_FILE_TMP}
sed -i "s/%vcloud_route_gw%/${vcloud_route_gw}/" ${NOVA_CONFIG_FILE_TMP}

cp ${NOVA_CONFIG_FILE_TMP} ${NOVA_CONFIG_FILE}

echo "config cinder..."

sed -i "s/%vcloud_host_ip%/${vcloud_host_ip}/" ${CINDER_CONFIG_FILE_TMP}
sed -i "s/%vcloud_org%/${vcloud_org}/" ${CINDER_CONFIG_FILE_TMP}
sed -i "s/%vcloud_vdc%/${vcloud_vdc}/" ${CINDER_CONFIG_FILE_TMP}
sed -i "s/%vcloud_host_username%/${vcloud_host_username}/" ${CINDER_CONFIG_FILE_TMP}
sed -i "s/%vcloud_host_password%/${vcloud_host_password}/" ${CINDER_CONFIG_FILE_TMP}


cp  ${CINDER_CONFIG_FILE_TMP}  ${CINDER_CONFIG_FILE}

echo "config success"
exit 0

