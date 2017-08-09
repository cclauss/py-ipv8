import logging

from cryptography.hazmat.primitives.asymmetric import ec

from ..keyvault.keys import Key
from .private.libnacl import LibNaCLSK
from .private.m2crypto import M2CryptoSK
from .public.libnacl import LibNaCLPK
from .public.m2crypto import M2CryptoPK

# We want to provide a few default curves.  We will change these curves as new become available and
# old ones to small to provide sufficient security.
_CURVES = {u"very-low": (ec.SECT163K1, "M2Crypto"),
           u"low": (ec.SECT233K1, "M2Crypto"),
           u"medium": (ec.SECT409K1, "M2Crypto"),
           u"high": (ec.SECT571R1, "M2Crypto"),
           u'curve25519': (None, "libnacl")}

logger = logging.getLogger(__name__)


class ECCrypto(object):
    """
    A crypto object which provides a layer between Dispersy and low level eccrypographic features.

    Most methods are implemented by:
        @author: Boudewijn Schoon
        @organization: Technical University Delft
        @contact: dispersy@frayja.com

    However since then, most functionality was completely rewritten by:
        @author: Niels Zeilemaker
    """

    @property
    def security_levels(self):
        """
        Returns the names of all available curves.
        @rtype: [unicode]
        """
        return _CURVES.keys()

    def generate_key(self, security_level):
        """
        Generate a new Elliptic Curve object with a new public / private key pair.

        Security can be u'low', u'medium', or u'high' depending on how secure you need your Elliptic
        Curve to be.  Currently these values translate into:
            - very-low: NID_sect163k1  ~42 byte signatures
            - low:      NID_sect233k1  ~60 byte signatures
            - medium:   NID_sect409k1 ~104 byte signatures
            - high:     NID_sect571r1 ~144 byte signatures

        Besides these predefined curves, all other curves provided by M2Crypto are also available.  For
        a full list of available curves, see ec_get_curves().

        @param security_level: Level of security {u'very-low', u'low', u'medium', or u'high'}.
        @type security_level: unicode
        """
        assert isinstance(security_level, unicode)
        assert security_level in _CURVES

        curve = _CURVES[security_level]
        if curve[1] == "M2Crypto":
            return M2CryptoSK(curve[0])

        if curve[1] == "libnacl":
            return LibNaCLSK()

    def key_to_bin(self, ec):
        "Convert the key to a binary format."
        assert isinstance(ec, Key), ec
        return ec.key_to_bin()

    def key_to_hash(self, ec):
        "Get a hash representation from a key."
        assert isinstance(ec, Key), ec
        return ec.key_to_hash()

    def is_valid_private_bin(self, string):
        "Returns True if the input is a valid public/private keypair stored in a binary format"
        try:
            self.key_from_private_bin(string)
        except:
            return False
        return True

    def is_valid_public_bin(self, string):
        "Returns True if the input is a valid public key"
        try:
            self.key_from_public_bin(string)
        except:
            return False
        return True

    def key_from_private_bin(self, string):
        "Get the EC from a public/private keypair stored in a binary format."
        if string.startswith("LibNaCLSK:"):
            return LibNaCLSK(string[10:])
        return M2CryptoSK(keystring=string)

    def key_from_public_bin(self, string):
        "Get the EC from a public key in binary format."
        if string.startswith("LibNaCLPK:"):
            return LibNaCLPK(string[10:])
        return M2CryptoPK(keystring=string)

    def get_signature_length(self, ec):
        """
        Returns the length, in bytes, of each signature made using EC.
        """
        assert isinstance(ec, Key), ec
        return ec.get_signature_length()

    def create_signature(self, ec, data):
        """
        Returns the signature of DIGEST made using EC.
        """
        assert isinstance(ec, Key), ec
        assert isinstance(data, str), type(data)
        return ec.signature(data)

    def is_valid_signature(self, ec, data, signature):
        """
        Returns True when SIGNATURE matches the DIGEST made using EC.
        """
        assert isinstance(ec, Key), ec
        assert isinstance(data, str), type(data)
        assert isinstance(signature, str), type(signature)

        try:
            return ec.verify(signature, data)
        except:
            return False