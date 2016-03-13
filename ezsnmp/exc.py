class SNMPError(Exception):
    '''SNMP Exception

    Should be fed with SNMP error_status and error_index'''
    pass


class SNMPTimeout(Exception):
    '''Will be raised if a timeout occured.

    If the SNMP community is wrong, the device doesn't respond to the SNMP
    request. A timeout could therefore also mean that there is a SNMP community
    mismatch.
    '''
    pass
