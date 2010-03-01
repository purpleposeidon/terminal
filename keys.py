# -*- coding: utf-8 -*-


import sys

import escape


all_keys = {}

def add_key(value, keystate):
  if type(value) == list:
    for val in value:
      all_keys[val] = keystate
  else:
    all_keys[value] = keystate



class SpecialKey:
  #A named key
  def __init__(self, name, value):
    if isinstance(name, str):
      #If a string, then there are no modifiers given
      name = KeyState(name)
    self.name = name
    self.value = value
    add_key(self.value, self.name)
  
  def __str__(self):
    return "<{0}>".format(self.name)
  __repr__ = __str__

class EscKey(SpecialKey):
  #Keys that start with an escape sequence
  def __init__(self, name, value):
    value = value.replace('\E', escape.ESC).replace('\e', escape.ESC)
    SpecialKey.__init__(self, name, value)


class ModKey:
  mods = ['2', {"shift":True}], ['3', {"alt": True}], ['4', {"shift":True, "alt":True}], ['5', {"ctrl":True}], ['6', {"shift":True, "ctrl":True}]
  def __init__(self, name, value):
    #Makes its own KeyState, okay?
    value = value.replace('\E', escape.ESC).replace('\e', escape.ESC)
    assert '*' in value
    if ';*' in value:
      #all_keys[value.replace(';*', '')] = KeyState(name)
      no_mod_val = value.replace(';*', '')
      add_key(no_mod_val, KeyState(name))
    else:
      all_keys[value.replace('*', '')] = KeyState(name)
    for mod_num, key_presses in ModKey.mods:
      k = KeyState(name, *key_presses)
      v = value.replace("*", mod_num)
      all_keys[v] = k

class KeyState:
  def __init__(self, value, shift=False, ctrl=False, alt=False, single=False):
    #If value is a single letter (w), it must be lower case.
    #If value is for a key name, it must be given in UPPER CASE
    self.value = value
    self.shift = shift
    self.ctrl = ctrl
    self.alt = alt
    self.single = single
  def meta(self):
    return KeyState(self.value, shift=self.shift, ctrl=self.ctrl, alt=True, single=False)
  def __str__(self):
    v = self.value
    if self.shift:
      v = v.upper()
      if v == self.value:
        v = 'Shift-'+self.value
      v = v.title()
    elif self.value == self.value.upper():
      v = v.title()
    if self.alt:
      v = 'Alt-'+v
    if self.ctrl:
      v = 'Ctrl-'+v
    if len(v) == 1:
      return v+"-key"
    return v
  __repr__ = __str__


#CtrlKey is the easiest
ctrl_offset = 64
for dalpha in range(27):
  SpecialKey(KeyState(chr(ctrl_offset+dalpha), ctrl=True), chr(dalpha))


def nonce_key(c):
  if (c.upper() == c) and (c.lower() != c):
    return KeyState(c, shift=True, single=True)
  else:
    return KeyState(c, single=True)

ESCAPE_ENDS = "~ ?\n\t\a"+escape.ESC #These would never show up inside an escape
#I think...


def key_stream(fd, **kwargs):
  #Yield KeyState
  
  while 1:
    for key in get_key(fd, **kwargs):
     yield key

def get_key(fd, empty_is_eof=False, show_esc_fail=True):
  try: c = fd.read(1)
  except IOError: c = ''
  if c == '':
    if empty_is_eof:
      raise EOFError
    return
  if c == escape.ESC:
    while 1:
      try: n = fd.read(1)
      except IOError: n = ''
      if n == '':
        #XXX If you wanted, you might be willing to look again really quickly!
        break
      c += n #We'll have at least two characters
      result = all_keys.get(c, None)
      if result:
        yield result
        return
      elif len(c) > 7 or n in ESCAPE_ENDS:
        #There's definitly something wrong!
        break
    
    if len(c) == 2:
      #It's a meta key
      char = c[1]
      k = all_keys.get(char, nonce_key(char))
      yield k.meta()
    elif show_esc_fail:
      #It's nothing that we know about
      for char in c:
        yield all_keys.get(char, nonce_key(char))
  else:
    #A single key!
    if c == '\r':
      #Err, skip that.
      return
    yield all_keys.get(c, nonce_key(c))


#'''
#Key data
EscKey("ESC", "\e")
SpecialKey("TAB", "\t")
EscKey(KeyState("TAB", shift=True), "\e[Z")
SpecialKey("ENTER", '\n')
EscKey(KeyState("ENTER", shift=True), '\eOM')
SpecialKey("BACKSPACE", '\x7f')
EscKey("UP", '\EA')
EscKey("DOWN", '\EB')
EscKey("RIGHT", '\EC')
EscKey("LEFT", '\ED')

EscKey("UP", '\E0A')
EscKey("DOWN", '\E0B')
EscKey("RIGHT", '\E0C')
EscKey("LEFT", '\E0D')

EscKey("UP", '\E[A')
EscKey("DOWN", '\E[B')
EscKey("RIGHT", '\E[C')
EscKey("LEFT", '\E[D')

ModKey("UP", "\E[1;*A")
ModKey("DOWN", "\E[1;*B")
ModKey("LEFT", "\E[1;*C")
ModKey("RIGHT", "\E[1;*D")

#TODO: "breaks the keypad in Vim"


EscKey("HOME", "\E[H")
EscKey("END", "\E[F")
EscKey("HOME", "\EOH")
EscKey("END", "\EOF")
ModKey("HOME", "\E[1;*H")
ModKey("END", "\E[1;*F")

EscKey("F1", "\EOP")
EscKey("F2", "\EOQ")
EscKey("F3", "\EOR")
EscKey("F4", "\EOS")
EscKey("F5", "\E[15~")
EscKey("F6", "\E[17~")
EscKey("F7", "\E[18~")
EscKey("F8", "\E[19~")
EscKey("F9", "\E[20~")
EscKey("F10", "\E[21~")
EscKey("F11", "\E[23~")
EscKey("F12", "\E[24~")

ModKey("F1", "\EO*P")
ModKey("F2", "\EO*Q")
ModKey("F3", "\EO*R")
ModKey("F4", "\EO*S")
ModKey("F5", "\E[15;*~")
ModKey("F6", "\E[17;*~")
ModKey("F7", "\E[18;*~")
ModKey("F8", "\E[19;*~")
ModKey("F9", "\E[20;*~")
ModKey("F10", "\E[21;*~")
ModKey("F11", "\E[23;*~")
ModKey("F12", "\E[24;*~")

SpecialKey(KeyState("SPACE", ctrl=True), "\x00")

SpecialKey("INSERT", "\E[2~")
SpecialKey("DELETE", "\E[3~")
ModKey("INSERT", "\E[2;*~")
ModKey("DELETE", "\E[3;*~")


##### Other keys, not copied from the Konsole dev's
SpecialKey("SPACE", ' ')
EscKey("PAGE UP", "\E[5~")
EscKey("PAGE DOWN", "\E[6~")
ModKey("PAGE UP", "\E[5;*~") #XXX Mods don't match!
ModKey("PAGE DOWN", "\E[6;*~") #XXX Mods don't match!
#I think part of the problem is that most terminals scroll up with this...

#'''




if __name__ == '__main__':
  try:
    escape.term_setup(sys.stdin)
    for _ in key_stream(sys.stdin):
      print _
  except (KeyboardInterrupt, EOFError):
    pass
  finally:
    escape.cleanup()