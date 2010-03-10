# -*- coding: utf-8 -*-
"""
An implementation of lineread for child windows
"""
import sys
sys.path.append("./")

import window
import keys

w = window.Window("Remote key obtainer")
for key in keys.stream(w):
  print key

