# -*- coding: utf-8 -*-
"""
An implementation of lineread for child windows
"""
import sys
sys.path.append("./")
import select

import window
import keys

w = window.Window("Remote key obtainer")
select.select([w], [],[])
for key in keys.stream(w):
  if key:
    print key
  select.select([w], [],[])

