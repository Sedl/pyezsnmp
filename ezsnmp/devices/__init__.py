from .. import EzSNMP


class BaseDevice(EzSNMP):

    def sysdescr(self):
        '''Returns the SNMPv2-MIB::sysDescr.0 string of the device

        Returns:
            SNMPv2-MIB::sysDescr.0
        '''
        descr = self.get((1, 3, 6, 1, 2, 1, 1, 1, 0))
        return str(descr[0][1])

    def walk_iftype(self):
        '''Queries IF-MIB::ifType (1.3.6.1.2.1.2.2.1.3)

        * ethernetCsmacd(6)
        * docsCableMaclayer(127)
        * docsCableDownstream(128)
        * docsCableUpstream(129)
        * other(1)

        Returns:
            dict - {oid: iftype}
        '''
        iftypes = {oid[-1]: val for oid, val in self.walk_iter(
                (1, 3, 6, 1, 2, 1, 2, 2, 1, 3), convert=int)}
        return iftypes

    def walk_ifname(self):
        '''IF-MIB::ifName (1.3.6.1.2.1.31.1.1.1.1)

        On Cisco systems this is usually the short name of the interface.
        Example: `Te4/1/0`

        If you want the full name of the interface, use :func:`walk_ifdescr`

        Returns:
            dict - {oid: ifname}
        '''
        ifname = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 31, 1, 1, 1, 1), convert=str)}
        return ifname

    def walk_ifdescr(self):
        '''IF-MIB::ifDescr (1.3.6.1.2.1.2.2.1.2)

        On Cisco systems this is usually the long name of the interface.
        Example: `TenGigabitEthernet4/1/0`

        Returns:
            dict - {oid: ifdescr}
        '''
        ifdescr = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 2), convert=str)}
        return ifdescr

    def walk_ifalias(self):
        '''IF-MIB::ifAlias (1.3.6.1.2.1.31.1.1.1.18)

        This is usually the description you can set in the interface
        configuration.

        Returns:
            dict - {oid: ifalias}
        '''
        ifalias = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 31, 1, 1, 1, 18), convert=str)}
        return ifalias

    def walk_ifadminstatus(self):
        ''' IF-MIB::ifAdminStatus (1.3.6.1.2.1.2.2.1.7)

        Status values:
            up(1)
            down(2)
            testing(3)

        Returns:
            dict = {oid: ifadminstatus
        '''
        ifstatus = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 7),
            convert=int)}
        return ifstatus

    def walk_ifoperstatus(self):
        ''' IF-MIB::ifOperStatus (1.3.6.1.2.1.2.2.1.8)

        Status values:
            up(1)
            down(2)
            testing(3)
        '''
        ifoper = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 8),
            convert=int)}
        return ifoper

    def walk_ifstackstatus(self):
        '''IF-MIB::ifStackStatus (1.3.6.1.2.1.31.1.2.1.3)

        This function returns a dict of oids with a list of subinterfaces.
        You can use this to find the ports in a Cisco Port-channel interface.

        This also applies to CASA Systems CMTS upstream channels.
        Each physical channel has one or more logical subinterfaces.

        Returns:
            dict - {oid: [subinterfaceoid1, subinterfaceoid2, ...]}
        '''
        ifstack = {}
        for oid, val in self.walk_iter((1, 3, 6, 1, 2, 1, 31, 1, 2, 1, 3)):
            intf, subintf = oid[-2:]
            if intf not in ifstack:
                ifstack[intf] = []
            ifstack[intf].append(subintf)

        return ifstack
