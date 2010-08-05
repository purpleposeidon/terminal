#!/usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup

version = open('VERSION').read().strip()
rz = "purpleposeidonSPAM".replace("SPAM", '@g''ma''il.com')

setup(
  #Meta data
  name="terminal",
  version=version,
  author="James Royston",
  author_email=rz,
  description="A sweet-tongued terminal manipulation library",
  url="http://github.com/purpleposeidon/terminal/",
  license="GPLv3",

  #Package data
  packages=['terminal'],
)

#import sys
#
#if sys.version_info[0] == 3:
#  #tell the peep about our fancy codecs module
#  import codecs, fixed_codecs
#  oldversion = True
#  if hasattr(codecs, "_codecs_hack_version"):
#    if codecs._codecs_hack_version == fixed_codecs._codecs_hack_version:
#      oldversion = False
#    else:
#      "is old."
#  else:
#    state = "not installed."
#  if oldversion:
#    print("The codecs library that comes with python3 has a bug that breaks ")
