# -*- coding: utf-8 -*-
"""
An implementation of lineread for child windows
"""
import sys
sys.path.append("./")
import random
import time

import window
import escape

w = window.Window("Remote line reader", recreate=False)
w.config(w.input_mode("R"))
while 1:
  #w.write('\r'+str(escape.CursorUp)+str(escape.ClearLine)+str(random.random())+'\n')
  #w.write(str(random.random())+'\n')
  w.write('\r'+str(escape.ClearLine)+str(random.random())+'\n')
  try:
    rez = w.read()
    if rez:
      sys.stdout.write(rez)
  except: pass
  time.sleep(.5)
