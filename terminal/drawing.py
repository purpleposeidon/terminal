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

import time
import weakref

import escape
import window
import basecolor

class Character:
  def dup(self):
    """If you're going to be manipulating characters (or colors) on an individual basis,
    you'll need to duplicate them. Otherwise, all of them will change!"""
    return Character(self.symbol, self.attr)
  
  def __init__(self, symbol, attr=basecolor.GRAY):
    self.symbol = symbol
    self.attr = attr
  
  def follow(self, old):
    return self.attr.follow(old)+str(self.symbol)

  def __repr__(self):
    return "%s%r%s" % (self.attr, self.symbol, escape.NORMAL)

EMPTY_CHAR = Character(' ')

class CharacterBuffer:
  def __init__(self, dims, fd, offset=(0, 0)):
    self.width, self.height = dims
    self.cfd = fd
    self.dx, self.dy = offset
    
    self.buff = {} #form [(x, y)] = Character
    self.changed = {} #form [(x, y)] = Character
    self.needs_full_redraw = True
    self.draw()

  def resize(self, width, height):
    if (self.width, self.height) != (width, height):
      if (width < self.width) or (height < self.height):
        self.needs_full_redraw = True
      self.width = width
      self.height = height

  def set_fd(self, fd):
    if self.cfd != fd:
      self.cfd = fd
      self.needs_full_redraw = True

  def add(self, x, y, char, attr=basecolor.GRAY):
    """
    Set a drawing.Character or a str at position x, y.
    attr is used to set color, bold, and such. It is only used with str
    """
    #Put char at x, y
    if isinstance(char, Character):
      if self.buff.get((x, y), None) != char:
        self.changed[(x, y)] = char
        self.buff[(x, y)] = char
    else:
      for c in char:
        self.add(x, y, Character(c, attr=attr))
        x += 1
  
  def redraw(self):
    #Re-draw everything in full
    self.cfd.write(str(escape.CursorHome))
    if self.dy:
      #Top offset
      self.cfd.write(escape.CursorDown(self.dy))
    last_attr = None
    for y in range(self.height):
      if self.dx:
        self.cfd.write(escape.CursorRight(self.dx)) #Left offset
      for x in range(self.width):
        c = self.buff.get((x, y), EMPTY_CHAR)
        self.cfd.write(c.follow(last_attr))
        last_attr = c.attr
      self.cfd.write(str(escape.CursorReturn)+str(escape.NewLine))
    self.needs_full_redraw = False
    self.changed = {}
    self.cfd.flush()
  
  def draw(self):
    if self.needs_full_redraw:
      self.redraw()
      return
    cx = cy = None
    last_attr = None
    #self.cfd.write(str(escape.CursorHome))
    for y in range(self.height):
      for x in range(self.width):
        c = self.changed.get((x, y))
        
        if c:
          #Put the cursor in proper position.
          #This is probably where the most optimization can come from
          if cx == cy == None:
            if x == y == 0:
              self.cfd.write(str(escape.CursorHome))
            else:
              self.cfd.write(escape.CursorSet(x+self.dx+1, y+self.dy+1))
          elif x == 0 and (cy+1 == y):
            self.cfd.write(escape.NewLine())
          elif (cx+1 == x) and (cy == y):
            pass #Just to the right, so do nothing
          elif (cx == x) and (cy != y):
            #Just move the y cursor
            self.cfd.write(escape.CursorDown(cy-y))
          elif (cy == y) and (cx != x):
            self.cfd.write(escape.CursorRight(x-cx))
          else:
            self.cfd.write(escape.CursorSet(y+self.dy+1, x+self.dx+1))
          self.cfd.write(c.follow(last_attr))
          last_attr = c.attr
          cx, cy = x, y
    self.changed = {}
    if not (cx == cy == None):
      self.cfd.flush()

class WindowBuffer(window.Window, CharacterBuffer):
  def __init__(self, title="Drawing Window"):
    """
    A CharacterBuffer that resides in a new window
    """
    #self.window = window.Window(title=title)
    window.Window.__init__(self, title=title)
    fail = 0
    while not self.size:
      self.ask_size()
      time.sleep(.01*fail**2+.01)
      self.read()
      fail += 1
      if fail == 10:
        raise Exception("Window did not tell us the size!")
    self.old_size = self.size
    CharacterBuffer.__init__(weakref.proxy(self), self.size, weakref.proxy(self)) #proxy so that there isn't a circular ref.
    
  def draw(self):
    if self.old_size != self.size:
      self.needs_full_redraw = True
      self.old_size = self.size
    CharacterBuffer.draw(self)


def test():
  import sys, time
  import rgbcolor
  import basecolor
  if len(sys.argv) == 1:
    cb = CharacterBuffer([25, 4], sys.stdout)
  else:
    cb = WindowBuffer()
  cb.add(0, 0, Character(':'))
  cb.add(1, 0, Character('D'))
  cb.add(0, 1, Character("!"))
  cb.draw()
  time.sleep(.5)
  cb.draw()
  cb.add(0, 0, Character('X'))
  cb.draw()
  time.sleep(.5)
  cb.draw()
  cb.add(1, 1, "This is a test!", basecolor.RED)
  cb.add(1, 2, "This is another test!", rgbcolor.Color(fg=rgbcolor.RgbColor(2, 3, 4)))
  cb.draw()
  time.sleep(.5)
  cb.redraw()

if __name__ == '__main__':
  test()

