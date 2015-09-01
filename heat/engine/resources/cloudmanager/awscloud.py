# -*- coding:utf-8 -*-
__author__ = 'q00222219@huawei'

from cloud import Cloud


class AwsCloud(Cloud):

    def __init__(self, cloud_id, region, az, access_key_id, secret_key,
                 cascaded_openstack, api_vpn, tunnel_vpn, proxy_info=None, access="True"):
        """Initialize AwsCloud.
        """
        Cloud.__init__(self, cloud_id, cascaded_openstack, api_vpn, tunnel_vpn, proxy_info, access)
        self.region = region
        self.az = az
        self.access_key_id = access_key_id
        self.secret_key = secret_key

