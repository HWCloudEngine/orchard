class FsCloud(object):

    def __init__(self, cloud_id, azName, dc,cloud_proxy=None,keystone_url=None,associate_user_id=None,
                 associate_admin_id=None,associate_service_id=None):
        self.cloud_id = cloud_id
        self.azName = azName
        self.dc = dc
        self.cloud_proxy = cloud_proxy
        self.keystone_url =keystone_url
        self.associate_user_id = associate_user_id
        self.associate_admin_id =associate_admin_id
        self.associate_service_id = associate_service_id
    

    def get_vpn_conn_name(self):
        vpn_conn_name = {"api_conn_name": self.cloud_id + '-api',
                         "tunnel_conn_name": self.cloud_id + '-tunnel'}
        return vpn_conn_name

    