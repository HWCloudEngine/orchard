#!/bin/sh
AWS_CONFIG_TEMPLATE=aws_config.template
AWS_CONFIG_FILE=./patches_tool/aws_patch/aws_config.ini

create_config_file() {
    if [ -f ${AWS_CONFIG_FILE} ]; then
        echo "delete aws_config.ini ..."
        rm ${AWS_CONFIG_FILE}
    fi
    echo "copy aws_config.ini ..."
    cp ${AWS_CONFIG_TEMPLATE} ${AWS_CONFIG_FILE}
}

config_dns() {
    dns=$1
    echo "config dns ..."
    sed -i "s/%dns%/${dns}/" ${AWS_CONFIG_FILE}
    echo "config dns success."
}

config_aws() {
    access_key_id=$1
    secret_key=$2
    aws_region=$3
    availability_zone=$4
	api_subnet_id=$5
    data_subnet_id=$6
    cgw_id=$7
    cgw_ip=$8
    openstack_az_host_ip=${9}
    echo "config aws ..."
    sed -i "s#%access_key_id%#${access_key_id}#" ${AWS_CONFIG_FILE}
    sed -i "s#%secret_key%#${secret_key}#" ${AWS_CONFIG_FILE}
    sed -i "s/%aws_region%/${aws_region}/" ${AWS_CONFIG_FILE}
    sed -i "s/%availability_zone%/${availability_zone}/" ${AWS_CONFIG_FILE}
    sed -i "s/%data_subnet_id%/${data_subnet_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%api_subnet_id%/${api_subnet_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%cgw_id%/${cgw_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%cgw_ip%/${cgw_ip}/" ${AWS_CONFIG_FILE}
	echo "openstack_az_host_ip="${openstack_az_host_ip}
    sed -i "s/%openstack_az_host_ip%/${openstack_az_host_ip}/" ${AWS_CONFIG_FILE}
    echo "config aws success"
}

config_route() {
    openstack_api_subnet=$1
    aws_api_gw=$2
    openstack_tunnel_subnet=$3
    aws_tunnel_gw=$4

    echo "config vm route ..."
    #vm_route=${openstack_api_subnet}":"${aws_api_gw}","${openstack_tunnel_subnet}":"${aws_tunnel_gw}

    vm_route=${aws_tunnel_gw}
	echo "vm_route="${vm_route}
    sed -i "s#%vm_route%#${vm_route}#" ${AWS_CONFIG_FILE}
    echo "config dns success"
}

config_hypernode_api() {
    cidr_vms=${1}
    cidr_hns=${2}
    data_subnet_id=${3}
    internal_base_subnet_id=${4}
    hn_image_id=${5}
    vpc_id=${6}
    internal_base_ip=${7}
    tunnel_gw_ip=${8}

    sed -i "s#%cidr_vms%#${cidr_vms}#" ${AWS_CONFIG_FILE}
    sed -i "s#%cidr_hns%#${cidr_hns}#" ${AWS_CONFIG_FILE}
    sed -i "s/%data_subnet_id%/${data_subnet_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%internal_base_subnet_id%/${internal_base_subnet_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%hn_image_id%/${hn_image_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%vpc_id%/${vpc_id}/" ${AWS_CONFIG_FILE}
    sed -i "s/%internal_base_ip%/${internal_base_ip}/" ${AWS_CONFIG_FILE}
    sed -i "s/%tunnel_gw_ip%/${tunnel_gw_ip}/" ${AWS_CONFIG_FILE}
}

conf_cinder_keystone_auth_token() {
    cascading_domain=${1}
    sed -i "s#%cascading_domain%#${cascading_domain}#" ${AWS_CONFIG_FILE}
}


if [ $# != 21 ]; then
    echo "Usage: sh $0 dns access_key_id secret_key aws_region availability_zone api_subnet_id data_subnet_id cgw_id cgw_ip openstack_az_host_ip openstack_api_subnet aws_api_gw openstack_tunnel_subnet aws_tunnel_gw cidr_vms cidr_hns internal_base_subnet_id hn_image_id vpc_id internal_base_ip cascading_domain"
    exit 1
fi
create_config_file
config_dns $1
config_aws $2 $3 $4 $5 $6 $7 $8 $9 ${10}
config_route ${11} ${12} ${13} ${14}
config_hypernode_api ${15} ${16} ${7} ${17} ${18} ${19} ${20} ${14}
conf_cinder_keystone_auth_token ${21}
