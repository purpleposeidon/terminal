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

