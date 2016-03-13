
from pysnmp.entity.rfc3413.oneliner import cmdgen
#   from pysnmp.proto import rfc1902
from pyasn1.type.univ import ObjectIdentifier

from .exc import SNMPTimeout
from .exc import SNMPError

CMDGEN = None


def get_cmdgen():
    '''Returns a pysnmp command generator object''

    Please don't instantiate this on every SNMP request. This produces a
    memory leak!

    Returns:
        :class:`pysnmp.entity.rfc3413.oneliner.cmdgen.CommandGenerator`
    '''
    global CMDGEN
    if not CMDGEN:
        CMDGEN = cmdgen.CommandGenerator()
    return CMDGEN


class EzSNMP():
    '''Makes the usage of SNMP a lot easier

    Args:
        host (str): hostname or IP address of the device

    Keyword Args:
        community (str): SNMP community
        port (int): SNMP port
        bulk (bool): If set to `True` bulk walks will be used.
            On most devices this is save.
        bulk_count (int): Number of SNMP values to get in one bulk request.
            If the packet is larger than the MTU of the device, the packet
            sent from the device will be fragmented. PySNMP handles this very
            well. The default value of 40 should provide a good balance
            between speed and packet fragmentation.
    '''

    def __init__(self, host, community='public', port=161, bulk=True,
                 bulk_count=40):

        #: If set to `False` don't use bulk requests
        self.bulk = bulk

        #: number of items to get in one GETBULK query
        self.bulk_count = bulk_count

        self._generator = get_cmdgen()

        #: :class:`pysnmp.entity.rfc3413.oneliner.cmdgen.CommunityData`
        self._comm_data = cmdgen.CommunityData(community)

        # TODO: IPv6 support
        #: :class:`pysnmp.entity.rfc3413.oneliner.cmdgen.UdpTransportTarget`
        self._transport = cmdgen.UdpTransportTarget((host, port))

        #: hostname
        self.host = host

    def walk(self, oid):
        '''Walks over all entries within the given OID subtree.

        If you are using bulk walks, there can be elements of other subtrees
        at the end of the returned list of OIDs. This is how SNMP works.
        You have to filter them out by yourself or use :func:`walk_iter`

        Args:
            oid (ObjectIdentifier): OID of the entry to walk over

        Returns:
            pysnmp var_binds

        Raises:
            SNMPError: SNMP device sends an error
            SNMPTimeout: A timeout occured
        '''
        if self.bulk:
            error_indication, error_status, error_index, \
                    var_binds = self._generator.bulkCmd(self._comm_data,
                                                        self._transport,
                                                        0,
                                                        self.bulk_count,
                                                        oid)

        else:
            error_indication, error_status, error_index, \
                    var_binds = self._generator.nextCmd(self._comm_data,
                                                        self._transport,
                                                        oid)
        if error_indication:
            if not error_status and not error_index:
                raise SNMPTimeout()
            else:
                raise SNMPError(error_status, error_index)
        return var_binds

    def walk_iter(self, oid, convert=None):
        '''Performs a SNMP walk with the given OID and returns a tuple with
        oid and value. This function will not return values from other
        SNMP trees than requested.

        Args:
            oid (ObjectIdentifier): the OID of the subtree to walk over
        Keyword Args:
            convert (function): used to convert the returned value
        '''

        if not isinstance(oid, ObjectIdentifier):
            oid = ObjectIdentifier(oid)

        for var in self.walk(oid):
            oid_ret, val = var[0]
            oid_tup = tuple(oid_ret)

            # check if we are in the same subtree as
            # requested or stop iteration
            if len(oid_tup) >= len(oid) and not oid_tup[:len(oid)] == oid:
                return

            if convert is not None:
                yield oid_ret, convert(val)
            else:
                yield oid_ret, val

    def get(self, oid):
        '''Gets a specific SNMP OID

        Args:
            oid (ObjectIdentifier)

        Raises:
            SNMPError:
            SNMPTimeout:
        '''
        error_indication, error_status, error_index, \
            var_binds = self._generator.getCmd(self._comm_data,
                                               self._transport,
                                               oid)
        if error_indication:
            if not error_status and not error_index:
                raise SNMPTimeout()
            else:
                raise SNMPError(error_status, error_index)
        return var_binds

    def set(self, oid, value):
        '''Sets a specific SNMP OID

        Example of a DOCSIS cable modem reset:

        .. code-block:: python

           from pysnmp.proto import rfc1902
           self.set((1,3,6,1,2,1,69,1,1,3,0), rfc1902.Integer(1))

        Args:
            oid (ObjectIdentifier): OID of the item to set
            value: See module pysnmp.proto.rfc1902 for a complete list of
              supported types.

        Raises:
            SNMPError:
            SNMPTimeout:
        '''
        error_indication, error_status, error_index, \
            var_binds = self._generator.setCmd(self._comm_data,
                                               self._transport,
                                               (oid, value))
        if error_indication:
            if not error_status and not error_index:
                raise SNMPTimeout()
            else:
                raise SNMPError(error_status, error_index)
        return var_binds
