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
This module contains escape sequences. For them to take effect, write them to the terminal. Some escape sequences can take arguments. Call the escape sequence with the arguments.

COLORS
======
All the possible colors available on a typical linux terminal are defined. There are two types: Base colors, and modified colors. Only base colors may be set to the background.
Base Colors:
  BLACK
  RED
  GREEN
  BROWN
  BLUE
  PURPLE
  CYAN
  GRAY

Modified Colors:
  DARK_GRAY
  WHITE
  ORANGE
  LIGHT_GREEN
  LIGHT_BLUE
  YELLOW
  LIGHT_CYAN
  PINK

You can mix colors for foreground and background by doing:
  Color(fg_color, bg_color)

Example:
  print Color(LIGHT_BLUE, BLUE)
This will set the terminal to write text using a light-blue, and the background would be dark-blue. Since LIGHT_BLUE is a modified color, Color(LIGHT_BLUE, LIGHT_BLUE) would have the same effect.


ATTRIBUTES
==========
NORMAL: Default color and style
BRIGHT: Makes the text brighter, bolder, and may change the color a bit
UNDERLINE: Underlines text
BLINK: Makes the text blink slowly and annoyingly
REVERSE: Flips the fg and the bg
BOLD: an alias for BRIGHT

MOVEMENT
========
CursorHome: Move cursor to the top-left corner
CursorUp(how_far=1): Moves the cursor up how_far cells. Attempts to move the cursor off the edge of the screen will just keep it at that extreme edge. The cursor won't enter any scrollback
CursorDown, CursorRight, CursorLeft: Operate the same.
CursorSet(line, col): (1, 1) is the first cell. Trying to move the cursor over the edge won't move it past, only to.
NewLine: Moves the cursor down, and to the very left.
CursorReturn: Moves the cursor to the left-hand side

ERASURE
=======
ClearLine: Clears the line the cursor is on. The cursor remains where it srarted.
ClearLineRight, ClearLineLeft: Clears the contents of the line to that direction, including what is underneath the cursor.
ClearScreen: Erases the contents of the screen. The cursor remains where it is
TerminalReset: Clears the screen, moves the cursor to (1, 1), and clears colors and attributes.

OTHER
=====
CursorHide, CursorShow: Hide/Show the cursor
TerminalTitle(name): Sometimes sets the terminal title. Sometimes fails badly.
NoScroll, YesScroll: Enable/disable the terminal's scroll buffer, it is often a separate from normal mode. Sometimes it has no effect. It is similiar to what vi does.

"""

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


CursorHome = AsciiCode("H") #Top-left
CursorEnd = AsciiCode('F') #Doesn't do anything. It's for the 'END' key.
CursorUp = AsciiCode("@A") #Attempts to move cursor offscreen have no uffect, even with a scrollback buffer
CursorDown = AsciiCode("@B") #To move the cursor by X chars, do CursorMOTION(X)
CursorRight = AsciiCode("@C") #If no argument is given to these ascii codes, it moves 1
CursorLeft = AsciiCode("@D")
CursorSet = AsciiCode("@;@H") #Line, Col.
NewLine = AsciiCode(value='\n')
CursorReturn = AsciiCode(value='\r')


ClearLine = AsciiCode("2K")
ClearLineRight = AsciiCode("K")
ClearLineLeft = AsciiCode("1K")
ClearScreen = AsciiCode("2J") #Cursor goes to bottom left. (see CursorHome)
TerminalReset = AsciiCode(sequence="c")

TerminalTitle = AsciiCode(sequence="]2;@\a") #Works with xterm. konsole/screen will print out part of the argument
CursorHide = AsciiCode("?25l")
CursorShow = AsciiCode("?25h")
NoScroll = AsciiCode("?1049h") #This puts it into a vi-like mode; no scrollbars on my terminal
YesScroll = AsciiCode("?1049l") #And this restores. Some terms don't erase the NoScroll content

class Color:
  def __init__(self, fg=None, bg=None, pattr=None, attr=None):
    if isinstance(bg, Color):
      #Can't set special foregrounds to background, sadly
      bg = bg.fg
    #if isinstance(fg, Color):
      #fg = fg.fg
    self.fg = fg
    self.bg = bg
    self.attr = attr
    self.pattr = pattr
  def __str__(self):
    #XXX I bet you can do "CSI attribute; attribute; attribute m"
    r = ''
    if self.pattr:
      r += CSI+str(self.pattr.val)+'m'
    if self.fg:
      r += str(self.fg)
      #r += CSI+str(self.fg.val)+'m'
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

styles = {'normal':NORMAL, 'bright': BRIGHT, 'underline': UNDERLINE, 'blink': BLINK, 'reverse': REVERSE, 'bold': BOLD}

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

colors = {'black':BLACK, 'red':RED, 'green':GREEN, 'brown':BROWN, 'blue':BLUE, 'purple':PURPLE, 'cyan':CYAN, 'gray':GRAY, 'dark gray':DARK_GRAY, 'white':WHITE, 'orange':ORANGE, 'light green':LIGHT_GREEN, 'light blue':LIGHT_BLUE, 'yellow':YELLOW, 'light cyan':LIGHT_CYAN, 'pink':PINK, 'default':NORMAL}


if __name__ == '__main__':
  import sys
  if '--help' in sys.argv or '-help' in sys.argv or '-?' in sys.argv:
    print """
Attributes demo:
  --style:  Show only styles
  --all:    Show each style with each color
"""
    raise SystemExit
  #print "Colors:"
  for color in colors:
    if not '--style' in sys.argv:
      print colors[color], color, NORMAL, CursorLeft(99), CursorRight(20), '(', color, ')'
  #print 'Styles:'
    if '--all' in sys.argv or '--style' in sys.argv:
      if '--style' in sys.argv: color = 'default'
      for style in styles:
        print '\t\t\t', colors[color], styles[style], style, NORMAL, CursorLeft(99), CursorRight(50), '(', style, ')'
      print '\t\t\t', colors[color], ''.join(str(_) for _ in styles.values()), 'every style', NORMAL, CursorLeft(99), CursorRight(50), '( every style )'
      print '\t\t\t', colors[color], '{0}{1}'.format(BOLD, REVERSE), 'bold reverse', NORMAL, CursorLeft(99), CursorRight(50), '( bold reverse )'
      if '--style' in sys.argv: break