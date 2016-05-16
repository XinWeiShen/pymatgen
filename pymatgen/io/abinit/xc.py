# coding: utf-8
# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License.
"""
"""
from __future__ import unicode_literals, division, print_function

from collections import namedtuple, OrderedDict
from monty.functools import lazy_property
from pymatgen.io.abinit.libxcfuncs import LibxcFuncs

class XcFunctional(object):
    """
    This object stores information about the XC correlation functional 
    used to generate the pseudo. The implementation is based on the libxc conventions 
    and is inspired to the XML specification for atomic PAW datasets documented at:

	https://wiki.fysik.dtu.dk/gpaw/setups/pawxml.html

    For convenience, part of the pawxml documentation is reported here.

    The xc_functional element defines the exchange-correlation functional used for 
    generating the dataset. It has the two attributes type and name.

    The type attribute can be LDA, GGA, MGGA or HYB.
    The name attribute designates the exchange-correlation functional 
    and can be specified in the following ways:

    [1] Taking the names from the LibXC library. The correlation and exchange names 
        are stripped from their XC_ part and combined with a + sign. 
        Here is an example for an LDA functional:

	    <xc_functional type="LDA", name="LDA_X+LDA_C_PW"/>

	and this is what PBE will look like:

	    <xc_functional type="GGA", name="GGA_X_PBE+GGA_C_PBE"/>

    [2] Using one of the following pre-defined aliases:

    type    name    LibXC equivalent             Reference
    LDA     PW      LDA_X+LDA_C_PW               LDA exchange; Perdew, Wang, PRB 45, 13244 (1992)
    GGA     PW91    GGA_X_PW91+GGA_C_PW91        Perdew et al PRB 46, 6671 (1992)
    GGA     PBE     GGA_X_PBE+GGA_C_PBE          Perdew, Burke, Ernzerhof, PRL 77, 3865 (1996)
    GGA     RPBE    GGA_X_RPBE+GGA_C_PBE         Hammer, Hansen, Nørskov, PRB 59, 7413 (1999)
    GGA     revPBE  GGA_X_PBE_R+GGA_C_PBE        Zhang, Yang, PRL 80, 890 (1998)
    GGA     PBEsol  GGA_X_PBE_SOL+GGA_C_PBE_SOL  Perdew et al, PRL 100, 136406 (2008)
    GGA     AM05    GGA_X_AM05+GGA_C_AM05        Armiento, Mattsson, PRB 72, 085108 (2005)
    GGA     BLYP    GGA_X_B88+GGA_C_LYP          Becke, PRA 38, 3098 (1988); Lee, Yang, Parr, PRB 37, 785
    """
    type_name = namedtuple("type_name", "type, name")
    
    xcf = LibxcFuncs
    aliases = OrderedDict([  # (x, c) --> type_name 
	((xcf.LDA_X, xcf.LDA_C_PW), type_name("LDA", "PW")),
	((xcf.GGA_X_PW91, xcf.GGA_C_PW91), type_name("GGA", "PW91")),
	((xcf.GGA_X_PBE, xcf.GGA_C_PBE), type_name("GGA", "PBE")),
	((xcf.GGA_X_RPBE, xcf.GGA_C_PBE), type_name("GGA", "RPBE")),
	((xcf.GGA_X_PBE_R, xcf.GGA_C_PBE), type_name("GGA", "revPBE")), 
	((xcf.GGA_X_PBE_SOL, xcf.GGA_C_PBE_SOL), type_name("GGA", "PBEsol")),
	((xcf.GGA_X_AM05, xcf.GGA_C_AM05), type_name("GGA", "AM05")),
	((xcf.GGA_X_B88, xcf.GGA_C_LYP), type_name("GGA", "BLYP")), 
    ])
    del type_name

    # Correspondence between Abinit ixc and libxc notation.
    # see: http://www.abinit.org/doc/helpfiles/for-v7.8/input_variables/varbas.html#ixc
    abinitixc_to_libxc = {
	"11": dict(x=xcf.GGA_X_PBE, c=xcf.GGA_C_PBE),
    }
    del xcf

    @classmethod 
    def known_names(cls):
	"""List of registered names."""
	return [nt.name for nt in cls.aliases.values()]

    @classmethod
    def from_abinit_ixc(cls, ixc_string):
        """Build the object from Abinit ixc (string)"""
        ixc = ixc_string.strip()
        if not ixc.startswith("-"):
            return cls(**cls.abinitixc_to_libxc[ixc])
        else:
            # libxc notation employed in Abinit: a six-digit number in the form XXXCCC or CCCXXX
	    assert len(ixc[1:]) == 6
            first, last = ixc[1:4], ixc[4:]
            x, c = LibxcFuncs(int(first)), LibxcFuncs(int(last))
	    if not x.is_x_kind: x, c = c, x # Swap
            assert x.is_x_kind and c.is_c_kind
            return cls(x=x, c=c)

    @classmethod
    def from_name(cls, name):
        """Build the object from one of the registered named"""
	for k, type_name in cls.aliases.items():
	    if type_name.name == name: 
		if len(k) == 1: return cls(xc=k)
		if len(k) == 2: return cls(x=k[0], c=k[1])
		raise ValueError("Wrong key: %s" % k)

	raise ValueError("Cannot find name=%s in aliases" % name)

    def __init__(self, xc=None, x=None, c=None):
	"""
	Args:
	    xc: LibxcFuncs for XC functional.
	    x, c: LibxcFuncs for exchange and correlation part. Mutually exclusive with xc.
	"""
        # Consistency check
        if xc is None:
             if x is None or c is None:
                raise ValueError("x or c must be specified when xc is None")
        else:
             if x is not None or c is not None:
                raise ValueError("x and c should be None when xc is specified")

        self.xc, self.x, self.c = xc, x, c

    @lazy_property
    def type_name(self):
	"""String in the form `type-name` e.g. GGA-PBE"""
	return "-".join([self.type, self.name])

    @lazy_property
    def type(self):
	"""The type of the functional."""
	if self.xc in self.aliases: return self.aliases[self.xc].type
	xc = (self.x, self.c)
	if xc in self.aliases: return self.aliases[xc].type
	raise NotImplementedError()
	if self.xc is not None: return self.xc.type
	return "+".join([self.x.type, self.c.type])

    @lazy_property
    def name(self):
	"""
        The name of the functional. If the functional is not found in the aliases,
        the string has the form X_NAME+C_NAME
        """
	if self.xc in self.aliases: return self.aliases[self.xc].name
	xc = (self.x, self.c)
	if xc in self.aliases: return self.aliases[xc].name
	if self.xc is not None: return self.xc.name
	return "+".join([self.x.name, self.c.name])

    #def __repr__(self):
    #return "<%s: %s at %s>" % (self.name, self.__class__.__name__, id(self))
    #def __str__(self):
    def __repr__(self):
	 return "%s" % self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
	if other is None: return False
	if isinstance(other, XcFunctional): return self.name == other.name
	# assume other is a string
	return self.name == other

    def __ne__(self, other):
        return not self == other

    #@property
    #def refs(self):
