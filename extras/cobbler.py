import xmlrpclib

class Cobbler:
    def __init__(self, server, username, password):
        self.server = server
        self.url = "http://" + server + "/cobbler_api"
        self.username = username
        self.password = password

    def connect(self):
        self.session = xmlrpclib.Server(self.url)

    def login(self):
        self.token = self.session.login(self.username, self.password)

    def profiles(self):
        profiles = self.session.get_profiles()
        profile_names = []
        for profile in profiles:
            profile_names.append(profile['name'])
        return sorted(profile_names)

    def create_system(self, system):
        system_id = self.session.new_system(self.token)

        self.session.modify_system(system_id, 'name', system.name, self.token)
        self.session.modify_system(system_id, 'hostname', system.fqdn, self.token)
        self.session.modify_system(system_id, 'profile', system.profile, self.token)
        self.session.modify_system(system_id, 'gateway', system.gateway, self.token)

        for ifname, interface in system.interfaces.items():
            self.session.modify_system(system_id, 'modify_interface', {
                'macaddress-' + ifname: interface['hwaddr'],
                'ipaddress-' + ifname: interface['ipv4'],
                'subnet-' + ifname: interface['netmask'],
                'dnsname-' + ifname: interface['fqdn']
            }, self.token)

        self.session.modify_system(system_id, 'netboot_enabled', True, self.token)
        self.session.save_system(system_id, self.token)

    def remove_system(self, name):
        self.session.remove_system(name, self.token)

    def find_by_hostname(self, name):
        name = self.session.find_system({'hostname': name})
        return name

    def find_by_hwaddr(self, hwaddr):
        name = self.session.find_system({'mac_address': hwaddr})
        return name

class CobblerSystem:
    def __init__(self, name, fqdn, profile, gateway, interface, hwaddr, ipv4, netmask):
        self.name = name
        self.fqdn = fqdn
        self.profile = profile
        self.gateway = gateway
        self.interfaces = dict()
        self.interfaces[interface] = dict()
        self.interfaces[interface]['hwaddr'] = hwaddr
        self.interfaces[interface]['ipv4'] = ipv4
        self.interfaces[interface]['netmask'] = netmask
        self.interfaces[interface]['fqdn'] = fqdn

    def add_interface(self, interface, hwaddr, ipv4, netmask, fqdn):
        self.interfaces[interface] = dict()
        self.interfaces[interface]['hwaddr'] = hwaddr
        self.interfaces[interface]['ipv4'] = ipv4
        self.interfaces[interface]['netmask'] = netmask
        self.interfaces[interface]['fqdn'] = fqdn
