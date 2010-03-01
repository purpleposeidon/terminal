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



ESC = chr(27)
CSI = ESC+'['

class AsciiCode:
  """
  An ascii code is used to control the terminal. It can be created either like:
    AsciiCode(arg [, default=''])
  or
    AsciiCode(sequence='' [, default=''])
  By default, "arg" is prepended with "<Esc>[". If you pass sequence instead, it is prepended only with "<Esc>".
  If there is a '@' character, it is replaced with the value 'default' if the AsciiCode is passed to directly to print. However, if you call the asciicode object, it will expect an argument, and the '@' will be replaced with the given argument.
  """
  def __init__(self, arg=None, sequence="", default='', value=None):
    self.default = default
    if not value:
      if arg:
        self.sequence = CSI+arg
      else:
        self.sequence = ESC+sequence
    else:
      self.sequence = value
  def __str__(self):
    return self.sequence.replace("@", self.default)
  def __call__(self, *args):
    i = str(self.sequence)
    args = list(args)
    while '@' in i and args:
      i = i.replace('@', str(args.pop(0)), 1)
    if '@' in i or args:
      raise Exception("Argument count mismatch")
    #print(repr(i))
    return i


ClearLine = AsciiCode("2K")
ClearLineRight = AsciiCode("K")
ClearLineLeft = AsciiCode("1K")
ClearScreen = AsciiCode("2J") #Cursor goes to bottom left. (see CursorHome)
TerminalReset = AsciiCode(sequence="c")
TerminalTitle = AsciiCode("2;@\007") #Didn't work with konsole, maybe with yours?
CursorHome = AsciiCode("H") #Top-left
CursorEnd = AsciiCode('F') #Doesn't do anything. It's for the 'END' key.
CursorUp = AsciiCode("@A") #Attempts to move cursor offscreen have no uffect, even with a scrollback buffer
CursorDown = AsciiCode("@B") #To move the cursor by X chars, do CursorMOTION(X)
CursorRight = AsciiCode("@C")
CursorLeft = AsciiCode("@D")
CursorSet = AsciiCode("@;@H") #Line, Col.
CursorHide = AsciiCode("?25l")
CursorShow = AsciiCode("?25h")
NoScroll = AsciiCode("?1049h") #This puts it into a vi-like mode; no scrollbars on my terminal
YesScroll = AsciiCode("?1049l") #And this restores. Some terms don't erase the NoScroll content
NewLine = AsciiCode(value='\n')
CursorReturn = AsciiCode(value='\r')

class Color:
  def __init__(self, fg=None, bg=None, pattr=None, attr=None):
    self.fg = fg
    if isinstance(bg, Color):
      #Can't set special foregrounds to background, sadly
      bg = bg.fg
    self.bg = bg
    self.attr = attr
    self.pattr = pattr
  def __str__(self):
    #XXX I'm pretty sure that somehow you can do CSI attribute; attribute; attribute m
    r = ''
    if self.pattr:
      r += CSI+str(self.pattr.val)+'m'
    if self.fg:
      r += CSI+str(self.fg.val)+'m'
    if self.bg:
      r += CSI+str(self.bg.derived+10)+'m'
    if self.attr:
      r += CSI+str(self.attr.val)+'m'
    return r
  def __repr__(self):
    return repr(str(self))

class AttrNum:
  def __init__(self, val, derived=False):
    self.val = val
    if derived:
      self.derived = derived
    else:
      self.derived = self.val
  def __str__(self):
    return CSI+str(self.val)+'m'
  def __repr__(self):
    return repr(str(self))
  def __or__(self, other):
    return AttrNum(self.val | other.val)
    #return AttrNum(self.val | other.val, derived=self.val)

#Styles
NORMAL = AttrNum(0)
BRIGHT = AttrNum(1)
UNDERLINE = AttrNum(4)
BLINK = AttrNum(5)
REVERSE = AttrNum(7)
BOLD = BRIGHT

#Base colors
_BLACK = AttrNum(30)
_RED = AttrNum(31)
_GREEN = AttrNum(32)
_BROWN = AttrNum(33) #"yellow"
_BLUE = AttrNum(34)
_PURPLE = AttrNum(35) #"magenta"
_CYAN = AttrNum(36)
_GRAY = AttrNum(37) #"white"

#Colors with attributes
BLACK = Color(_BLACK, pattr=NORMAL)
RED = Color(_RED, pattr=NORMAL)
GREEN = Color(_GREEN, pattr=NORMAL)
BROWN = Color(_BROWN, pattr=NORMAL)
BLUE = Color(_BLUE, pattr=NORMAL)
PURPLE = Color(_PURPLE, pattr=NORMAL)
CYAN = Color(_CYAN, pattr=NORMAL)
GRAY = Color(_GRAY, pattr=NORMAL)

#Advanced colors (These can't be used in the background)
DARK_GRAY = Color(_BLACK, attr=BRIGHT)
WHITE = Color(_GRAY, attr=BRIGHT)
ORANGE = Color(_RED, attr=BRIGHT)
LIGHT_GREEN = Color(_GREEN, attr=BRIGHT)
LIGHT_BLUE = Color(_BLUE, attr=BRIGHT)
YELLOW = Color(_BROWN, attr=BRIGHT)
LIGHT_CYAN = Color(_CYAN, attr=BRIGHT)
PINK = Color(_PURPLE, attr=BRIGHT)

colors = {'black':BLACK, 'red':RED, 'green':GREEN, 'brown':BROWN, 'blue':BLUE, 'purple':PURPLE, 'cyan':CYAN, 'gray':GRAY, 'dark gray':DARK_GRAY, 'white':WHITE, 'orange':ORANGE, 'light green':LIGHT_GREEN, 'light blue':LIGHT_BLUE, 'yellow':YELLOW, 'light cyan':LIGHT_CYAN, 'pink':PINK}


import os, termios, fcntl, struct



def termsize():
  """ Returns the (height, width) of the terminal. Stolen from somewhere."""
  try:
    return int(os.environ["LINES"]), int(os.environ["COLUMNS"])
  except KeyError:
    #The above environ variables are rarely defined.
    height, width = struct.unpack(
      "hhhh", fcntl.ioctl(1, termios.TIOCGWINSZ ,"\000"*8))[0:2]
    if not height: return 25, 80
    return height, width 

import io
import sys
import atexit
import tempfile



#Handle input stuff...
fd = None
oldterm = None
newattr = None
oldflags = None

#stolen termios voodoo code is stolen magic voodoo.
#I've quite forgotten where it comes from.

@atexit.register
def cleanup(fd_=None):
  """Return terminal to sanity, remove plumbing"""
  global fd, oldterm, newattr, oldflags
  if fd_:
    use_fd = fd_
  else:
    use_fd = fd
  if use_fd is None:
    return #It wasn't set up to begin with!
  try:
    termios.tcsetattr(use_fd, termios.TCSAFLUSH, oldterm) #Stolen
    fcntl.fcntl(use_fd, fcntl.F_SETFL, oldflags) #Stolen
  except: pass
  

#This code is also stolen.
def term_setup(fd_=None):
  """Puts the terminal the way we want it. This code is also stolen.
  XXX Can only call it once per cleanup()"""
  global fd, oldterm, newattr, oldflags
  if fd_:
    fd = fd_
  else:
    fd = sys.stdin.fileno()
  
  oldterm = termios.tcgetattr(fd)
  newattr = oldterm[:]
  newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)
  
  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

