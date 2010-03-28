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

class PseudoString:
  def __add__(self, other): return str(self)+other
  def __radd__(self, other): return other+str(self)

class AsciiCode(PseudoString):
  """
  An ascii code is used to control the terminal. It can be created either like:
    AsciiCode(arg [, default=''])
  or
    AsciiCode(sequence='' [, default=''])
  of
    AsciiCode(value=... [, default=''])
  By default, "arg" is prepended with "<Esc>[". If you pass sequence instead, it is prepended only with "<Esc>". If you give instead a value, it will not prepend with "<Esc>"
  
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
    return i

CursorHome = AsciiCode("H") #Top-left
CursorEnd = AsciiCode('F') #Doesn't do anything. It's for the 'END' key.
CursorUp = AsciiCode("@A") #Attempts to move cursor offscreen have no uffect, even with a scrollback buffer
CursorDown = AsciiCode("@B") #To move the cursor by X chars, do CursorMOTION(X)
CursorRight = AsciiCode("@C") #If no argument is given to these ascii codes, it moves 1
CursorLeft = AsciiCode("@D")
CursorSet = AsciiCode("@;@H") #Line, Col.
CursorSave = AsciiCode("7")
CursorRestore = AsciiCode("8")
NewLine = AsciiCode(value='\n')
CursorReturn = AsciiCode(value='\r')
CursorPosition = AsciiCode(sequence="6n")


ClearLine = AsciiCode("2K")
ClearLineRight = AsciiCode("K")
ClearLineLeft = AsciiCode("1K")
ClearScreen = AsciiCode("2J") #Cursor goes to bottom left. (see CursorHome)
ClearScreenUp = AsciiCode("0J")
ClearScreenDown = AsciiCode("J")
TerminalReset = AsciiCode(sequence="c")

TerminalTitle = AsciiCode(sequence="]2;@\a") #Works with xterm. konsole/screen will print out part of the argument
CursorHide = AsciiCode("?25l")
CursorShow = AsciiCode("?25h")
NoScroll = AsciiCode("?1049h") #This puts it into a vi-like mode; no scrollbars on my terminal
YesScroll = AsciiCode("?1049l") #And this restores. Some terms don't erase the NoScroll content

#NumPad1 = AsciiCode("?1h")
#NumPad2 = AsciiCode(sequence="=")
ScrollRegion = AsciiCode("@;@r")
#ScrollUp = AsciiCode("D")
#ScrollDown = AsciiCode("M")

class AttrNum(PseudoString):
  def __init__(self, val, derived=False, name=None):
    self.val = val
    self.name = name
    if derived:
      self.derived = derived
    else:
      self.derived = self.val
  def __str__(self):
    return CSI+str(self.val)+'m'
  def __repr__(self):
    if self.name:
      return self.name
    return repr(str(self))
  def __or__(self, other):
    return AttrNum(self.val | other.val)
    #return AttrNum(self.val | other.val, derived=self.val)

#Styles
NORMAL = AttrNum(0, name="NORMAL")
BRIGHT = AttrNum(1, name="BRIGHT")
UNDERLINE = AttrNum(4, name="UNDERLINE")
BLINK = AttrNum(5, name="BLINK")
REVERSE = AttrNum(7, name="REVERSE")
BOLD = BRIGHT
#XXX Why are there holes? Something missing?

styles = {'normal':NORMAL, 'bright': BRIGHT, 'underline': UNDERLINE, 'blink': BLINK, 'reverse': REVERSE, 'bold': BOLD}

def test():
  import sys
  def write(*args):
    sys.stdout.write(' '.join(map(str, args))+'\n')
  if '--help' in sys.argv or '-help' in sys.argv or '-?' in sys.argv:
    write("""
Attributes demo:
  --style:  Show only styles
  --all:    Show each style with each color
""")
    raise SystemExit
  #print "Colors:"
  for color in colors:
    if not '--style' in sys.argv:
      write(colors[color], color, NORMAL, CursorLeft(99), CursorRight(20), '(', color, ')')
    
    if '--all' in sys.argv or '--style' in sys.argv:
      if '--style' in sys.argv: color = 'default'
      for style in styles:
        write('\t\t\t', colors[color], styles[style], style, NORMAL, CursorLeft(99), CursorRight(50), '(', style, ')')
      write('\t\t\t', colors[color], ''.join(str(_) for _ in styles.values()), 'every style', NORMAL, CursorLeft(99), CursorRight(50), '( every style )')
      write('\t\t\t', colors[color], '{0}{1}'.format(BOLD, REVERSE), 'bold reverse', NORMAL, CursorLeft(99), CursorRight(50), '( bold reverse )')
      if '--style' in sys.argv: break

if __name__ == '__main__':
  #test()
  pass
