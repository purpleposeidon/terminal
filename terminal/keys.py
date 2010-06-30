# -*- coding: utf-8 -*-

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

Bugs
  Numpad is a terrifying mess

Notes:
  If ctrl is used, case (shift vs. no shift) is lost. Assumes upper.
  Alt just proceeds whatever follows with an escape.
  Logo (Meta?) only works for ModKeys (F1, Home...)
"""

import sys
import time
import select

import escape
import coms
import window

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
  #Err, I guess? It's the logo...
  mods = (
    ['1', {"logo": True}],
    ['2', {"shift":True}],
    ['3', {"alt": True}],
    ['4', {"shift":True, "alt":True}],
    ['5', {"ctrl":True}],
    ['6', {"shift":True, "ctrl":True}],
    ['7', {"ctrl": True, "alt": True}],
    ['8', {"shift":True, "ctrl":True, "alt":True}],
  )
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
      k = KeyState(name, **key_presses)
      v = value.replace("*", mod_num)
      all_keys[v] = k

class KeyState:
  def __init__(self, value, shift=False, ctrl=False, alt=False, logo=False, single=False, character=None):
    #If value is a single letter (w), it must be lower case.
    #If value is for a key name, it must be given in UPPER CASE
    self.value = value
    self.shift = shift
    self.ctrl = ctrl
    self.alt = alt
    self.logo = logo
    self.single = single
    if not character:
      character = self.value
    self.character = character
  def meta(self):
    return KeyState(self.value, shift=self.shift, ctrl=self.ctrl, alt=True, single=False)
  def __in__(self, lizt):
    for l in lizt:
      if self == l:
        return True
  def __eq__(self, other):
    if isinstance(other, KeyState):
      return str(self) == str(other)
    if other is None: return False
    if str(self) == str(other):
      return True
    return str(other).lower() == self.value.lower()
  def __str__(self):
    v = self.value
    if self.shift:
      v = v.upper()
      #if (v == self.value) or (len(v) > 1):
      if (len(v) > 1):
        v = 'Shift-'+self.value.encode("utf")
      v = v.title()
    elif self.value == self.value.upper():
      v = v.title()
    v = v.encode("utf")
    if self.logo:
      v = 'Logo-'+v
    if self.alt:
      v = 'Alt-'+v
    if self.ctrl:
      v = 'Ctrl-'+v
    
    #if len(v) == 1:
    if (self.ctrl == self.alt == self.logo == False) and len(self.value) == 1:
      return v+"-key"
    else:
      return v #.title()
  __repr__ = __str__


#CtrlKey is the easiest
ctrl_offset = 64
for dalpha in range(32): #Hell with it...
  SpecialKey(KeyState(chr(ctrl_offset+dalpha), ctrl=True), chr(dalpha))


def nonce_key(c):
  
  #assert isinstance(c, unicode)
  if (c.upper() == c) and (c.lower() != c):
    return KeyState(c, shift=True, single=True)
  else:
    return KeyState(c, single=True)

ESCAPE_ENDS = "~ ?\n\t\a"+escape.ESC #These would never show up inside an escape
#I think...


def stream(fd=sys.stdin, intr_key=KeyState('C', ctrl=True), **kwargs):
  """
  ``fd'' is the file-like object. It defaults to stdin. If overiding, use coms.Input(filename).
  Iterator yields KeyState objects.
   ^S and ^Q doesn't do flow control, ^\ doesn't quit.
  ^C has been implemented, but it can be over-ridden. Set to None to prevent KeyboardInterrupt, or set to a different KeyState to change it.
  """
  
  fileno = None
  try:
    #Set up the terminal. (Could be a remote window, needs special treatment)
    if isinstance(fd, window.Window):
      fd.config(fd.input_mode('r'))
      #print `fd.config_string`
    else:
      fileno = fd.fileno()
      coms.DISABLE_TERM_SIG = True
      coms.apply_ctrl_settings(fileno)
    
    while 1:
      for key in get_key(fd, **kwargs):
        if key == intr_key:
          raise KeyboardInterrupt(str(key))
        yield key
      yield None
  finally:
    if fileno:
      coms.DISABLE_TERM_SIG = False
      coms.apply_ctrl_settings(fileno)

#This sets the maximum time to take while reading escape combos.
#.0002 seems to be the minimum. Determined by SSH'ing across the
#internet and back with DSL.
ESCAPE_DELAY = .0002*100

def get_key(fd, empty_is_eof=False, show_esc_fail=False, **kwargs):
  """
  This iterator does the work of yielding a KeyState.
  """
  try: c = fd.read(1)
  except IOError:
    return
  if c == '':
    if empty_is_eof:
      raise EOFError
    return
  if c == escape.ESC:
    start = time.time()
    end = start+ESCAPE_DELAY
    new_char = "XXX"
    #make sure blocking is on
    if fd.blocking:
      coms.noblock(fd)
    try:
      #Get shit
      while 1:
        #Add a new character
        #print("add a new character")
        escape_wait = ESCAPE_DELAY - (time.time() - start)
        if escape_wait < 0:
          break
        new_char = ''
        #fd.wait(escape_wait)
        try:
          new_char = fd.read(1)
        except IOError:
          pass
        c += new_char
        #See if it's anything
        if c in all_keys:
          #It's something specific, easy
          #print("specific key")
          yield all_keys[c]
          return
        else:
          #Either an incomplete key, or something we don't know
          #print("incomplete key")
          possible_key = False
          for key_string in all_keys:
            if key_string.startswith(c):
              possible_key = True
              break
          if not possible_key:
            break
      #end while 1
    finally:
      #turn off blocking
      if fd.blocking:
        coms.yesblock(fd)
    #It's not a specific character.
    #Either a meta character (Alt-c), or an unknown sequence
    if len(c) == 2:
      #Definitly Meta
      char = c[1]
      k = all_keys.get(char, nonce_key(char))
      yield k.meta()
      return

    raise Exception("Unknown escape sequence %r" % c)
  else:
    #Not an escape sequence, thank god.
    #It's a single key, or a ctrl key.
    if c == '\r':
      #Pay no attention.
      return
    #print `c`
    yield all_keys.get(c, nonce_key(c))


#'''
#Key data
EscKey(KeyState("ESC", single=True), "\e")
SpecialKey(KeyState("TAB", single=True, character='\t'), "\t")
EscKey(KeyState("TAB", shift=True, character='\t'), "\e[Z")
SpecialKey(KeyState("ENTER", single=True, character='\n'), '\n')
EscKey(KeyState("ENTER", shift=True, character='\n'), '\eOM')
SpecialKey(KeyState("BACKSPACE", single=True), '\x7f')

#These eat up meta-A 
#EscKey("UP", '\EA')
#EscKey("DOWN", '\EB')
#EscKey("RIGHT", '\EC')
#EscKey("LEFT", '\ED')

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

#ModKey takes care of cases where no modifier info is given
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
#(But they're probably listed there anyways. >_>)
SpecialKey(KeyState("SPACE", single=True, character=' '), ' ')
ModKey("PAGE UP", "\E[5;*~")
ModKey("PAGE DOWN", "\E[6;*~")

EscKey(KeyState("ENTER", alt=True, shift=True), "\E\EOM")
EscKey(KeyState("ESC", alt=True), "\E\E")
#SpecialKey(KeyState("/", ctrl=True), "\x1f")
#SpecialKey(KeyState("\\", ctrl=True), "\x1c") #QUIT, actually


#'''


def test():
  print("""Prints the keys you press. The following keys ought to be detected:
    a (ascii)
    ú (latin unicode)
    う(Fancy unicode. I only know how to copy-and-paste these; I'm not so sure about modifiers. You can try pressing Esc and quickly pasting it. It should come out as Alt-う.)
    Escape
    alt-u
    alt-ú (For me, left alt+right alt+u w/ international keyboard)
    Logo-F1
    Logo-Page Up (Logo only happens with this class of keys)
    Ctrl-Alt-Right


Exit with ctrl-C
  """)
  inp = coms.Input()
  try:
    select.select([inp], [],[])
    for _ in stream(inp):
      if _:
        sys.stdout.write(str(_)+'\n')
      select.select([inp], [],[])
  except (KeyboardInterrupt, EOFError):
    pass
  finally:
    inp.close()

if __name__ == '__main__':
  test()

