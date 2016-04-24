from socket import gaierror
from decimal import Decimal

from . import BaseDevice
from ..exc import SNMPTimeout


DOCS_DOWNSTR_TREE = (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 1, 1)
DOCS_UPSTR_TREE = (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 2, 1)


def t_startswith(tupa, tupb):
    if tupa < tupb:
        return False

    if tupa[:len(tupb)] == tupb:
        return True

    return False


class Modeminfo:
    '''Keeps a record of DOCSIS modem data

    All units are in Hertz and dBmV unless specified otherwise.

    Attributes:
        sysdescr (str): sysdescr
        down_freq (dict): dict of all downstream frequencies
        down_bw (dict): downstream channel bandwidth in Hertz
        down_mod (dict): downstream modulatio profile
            * unknown(1)
            * other(2)
            * qam64(3)
            * qam256(4)
        down_power (dict): downstream channel receive power in dBmV
        down_non_oper (list): list of impaired (non operating)
            downstream channels
        up_non_oper (list): list of all impaired (non operating) upstream
            channels
        error: can be one of
            * snmp_timeout: an SNMP timeout occured
            * dns_nxdomain: hostname couldn't be resolved

    '''
    __slots__ = [
        'sysdescr',
        'error',
        # downstreams
        'down_freq',
        'down_bw',
        'down_mod',
        'down_power',
        'down_non_oper',
        'down_snr',
        'down_cw_unerroreds',
        'down_cw_correcteds',
        'down_cw_uncorrectables',
        # upstreams
        'up_freq',
        'up_bw',
        'up_timingoffset',
        'up_non_oper',
    ]

    def __init__(self):
        self.sysdescr = None
        self.error = None

        #: DOCS-IF-MIB::docsIfDownChannelFrequency
        self.down_freq = {}

        #: DOCS-IF-MIB::docsIfDownChannelWidth
        self.down_bw = {}

        #: OCS-IF-MIB::docsIfDownChannelModulation
        self.down_mod = {}

        #: DOCS-IF-MIB::docsIfDownChannelPower
        self.down_power = {}

        #: non operational downstream channels
        self.down_non_oper = []

        #: SNR of downstream channels
        self.down_snr = {}

        #: downstream codewords unerrored
        self.down_cw_unerroreds = {}

        #: downstream codewords corrected
        self.down_cw_correcteds = {}

        #: downstream codewords uncorrectables
        self.down_cw_uncorrectables = {}

        #: upstream channel frequencies
        self.up_freq = {}

        #: upstream channel bandwidth in Hertz
        self.up_bw = {}

        #: upstream timing offset
        self.up_timingoffset = {}

        #: non operational upstream channels
        self.up_non_oper = []

    def to_dict(self):
        out_dict = {}
        for key in self.__slots__:
            val = getattr(self, key, None)
            # ignore empty attributes
            if not val:
                continue
            out_dict[key] = val
        return out_dict


class Modem(BaseDevice):
    '''Class for querying DOCSIS modems

    Don't use bulk walks with DOCSIS modems. Most of them don't
    support bulk walks and will trigger a SNMPTimeout exception.
    '''

    def walk_downstr_snr(self):
        '''DOCS-IF-MIB::docsIfSigQSignalNoise (1.3.6.1.2.1.10.127.1.1.4.1.5)
        Returns:
            dict - {oid: snr(float)}
        '''
        down_snr = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 4, 1, 5),
            convert=lambda x: float(Decimal(int(x))/10))}
        return down_snr

    def walk_downstr_cw_unerroreds(self):
        '''DOCS-IF-MIB::docsIfSigQExtUnerroreds (1.3.6.1.2.1.10.127.1.1.4.1.8)

        DOCSIS downsteam unerrored codewords
        '''
        down_unerrored = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 4, 1, 8),
            convert=int)}
        return down_unerrored

    def walk_downstr_cw_correcteds(self):
        '''DOCS-IF-MIB::docsIfSigQExtCorrecteds (1.3.6.1.2.1.10.127.1.1.4.1.9)

        DOCSIS downsteam corrected codewords
        '''
        down_corrected = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 4, 1, 9),
            convert=int)}
        return down_corrected

    def walk_downstr_cw_uncorrectables(self):
        '''DOCS-IF-MIB::docsIfSigQExtUncorrectables
        (1.3.6.1.2.1.10.127.1.1.4.1.10)

        DOCSIS downsteam uncorrectables (erroneous) codewords
        '''
        down_uncorr = {oid[-1]: val for oid, val in self.walk_iter(
            (1, 3, 6, 1, 2, 1, 10, 127, 1, 1, 4, 1, 10),
            convert=int)}
        return down_uncorr

    def get_all_info(self):
        mdata = Modeminfo()
        try:
            mdata.sysdescr = self.sysdescr()

            # operational status of interface
            # can be used to find impaired upstream and downstream channels
            if_oper = self.walk_ifoperstatus()

            # downstream channels
            oid2down = {}
            downstr_tree = self.walk_iter(DOCS_DOWNSTR_TREE)
            oidlen = len(DOCS_DOWNSTR_TREE)
            for oid, val in downstr_tree:
                oid = oid[oidlen:]

                # DOCS-IF-MIB::docsIfDownChannelId
                if oid[0] == 1:
                    oid2down[oid[1]] = int(val)
                    # check if downstream channel is operational
                    if oid[1] in if_oper and not if_oper[oid[1]] == 1:
                        mdata.down_non_oper.append(int(val))
                    continue

                num = oid2down[oid[1]]
                # DOCS-IF-MIB::docsIfDownChannelFrequency
                if oid[0] == 2:
                    # num = oid2down[oid[1]]
                    mdata.down_freq[num] = int(val)
                    continue

                # DOCS-IF-MIB::docsIfDownChannelWidth
                if oid[0] == 3:
                    # num =
                    mdata.down_bw[num] = int(val)
                    continue

                # OCS-IF-MIB::docsIfDownChannelModulation
                if oid[0] == 4:
                    mdata.down_mod[num] = int(val)
                    continue

                # DOCS-IF-MIB::docsIfDownChannelPower
                if oid[0] == 6:
                    # SNMP values are tenth dBmV so we have to divide it by 10
                    # use decimal calculation to prevent ugly floating point
                    # miscalculations
                    mdata.down_power[num] = float(Decimal(int(val)) / 10)

            # upstream channels
            oid2up = {}
            upstr_tree = self.walk_iter(DOCS_UPSTR_TREE)
            oidlen = len(DOCS_DOWNSTR_TREE)
            for oid, val in upstr_tree:
                oid = oid[oidlen:]

                # DOCS-IF-MIB::docsIfUpChannelId
                if oid[0] == 1:
                    oid2up[oid[1]] = int(val)
                    if oid[1] in if_oper and not if_oper[oid[1]] == 1:
                        mdata.up_non_oper.append(int(val))
                    continue

                num = oid2up[oid[1]]

                # DOCS-IF-MIB::docsIfUpChannelFrequency
                if oid[0] == 2:
                    mdata.up_freq[num] = int(val)
                    continue

                # DOCS-IF-MIB::docsIfUpChannelWidth
                if oid[0] == 3:
                    mdata.up_bw[num] = int(val)
                    continue

                # DOCS-IF-MIB::docsIfUpChannelTxTimingOffset
                if oid[0] == 6:
                    mdata.up_timingoffset[num] = int(val)
                    continue

            # downstream SNR
            # DOCS-IF-MIB::docsIfSigQSignalNoise
            for oid, val in self.walk_downstr_snr().items():
                num = oid2down[oid]
                mdata.down_snr[num] = val

            mdata.down_cw_correcteds = {
                oid2down[oid]: val for oid, val in
                self.walk_downstr_cw_correcteds().items()}
            mdata.down_cw_unerroreds = {
                oid2down[oid]: val for oid, val in
                self.walk_downstr_cw_unerroreds().items()}
            mdata.down_cw_uncorrectables = {
                oid2down[oid]: val for oid, val in
                self.walk_downstr_cw_uncorrectables().items()}

        except SNMPTimeout:
                mdata.error = 'snmp_timeout'
                return mdata

        except gaierror:
            mdata.error = 'dns_nxdomain'
            return mdata

        return mdata
