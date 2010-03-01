#!/usr/bin/python
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

import escape


class Character:
  def dup(self):
    """If you're going to be manipulating characters (or colors) on an individual basis,
    you'll need to duplicate them. Otherwise, all of them will change!"""
    return Character(self.symbol, self.attr)
  
  def __init__(self, symbol, attr=escape.GRAY):
    self.symbol = symbol
    self.attr = attr
  
  def format(self, old_attr=None):
    if old_attr == self.attr:
      return self.symbol
    else:
      return "%s%s" % (self.attr, self.symbol)

  def __repr__(self):
    return "%s%r%s" % (self.attr, self.symbol, escape.NORMAL)

EMPTY_CHAR = Character(' ')

class CharacterBuffer:
  def __init__(self, width, height, fd, offset=(0, 0)):
    self.width = width
    self.height = height
    self.fd = fd
    self.dx, self.dy = offset
    
    self.buff = {} #form [(x, y)] = Character
    self.changed = {} #form (x, y) = Character
    self.needs_full_redraw = True

  def resize(self, width, height):
    self.width = width
    self.height = height

  def set_fd(self, fd):
    if self.fd != fd:
      self.fd = fd
      self.needs_full_redraw = True

  def add(self, x, y, char, attr=escape.GRAY):
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
    #Re-draw everything
    self.fd.write(str(escape.CursorHome))
    if self.dy:
      #Top offset
      self.fd.write(escape.CursorDown(self.dy))
    last_attr = None
    for y in range(self.height):
      if self.dx:
        self.fd.write(escape.CursorRight(self.dx)) #Left offset
      for x in range(self.width):
        c = self.buff.get((x, y), EMPTY_CHAR)
        self.fd.write(c.format(last_attr))
        last_attr = c.attr
      self.fd.write(str(escape.CursorReturn)+str(escape.NewLine))
    self.needs_full_redraw = False
    self.changed = {}
    self.fd.flush()
  
  def draw(self):
    if self.needs_full_redraw:
      self.redraw()
      return
    cx = cy = None
    last_attr = None
    #self.fd.write(str(escape.CursorHome))
    for y in range(self.height):
      for x in range(self.width):
        c = self.changed.get((x, y))
        
        if c:
          #Put the cursor in proper position.
          #This is probably where the most optimization can come from
          if cx == cy == None:
            if x == y == 0:
              self.fd.write(str(escape.CursorHome))
            else:
              self.fd.write(escape.CursorSet(x+self.dx+1, y+self.dy+1))
          elif x == 0 and (cy+1 == y):
            self.fd.write(escape.NewLine())
          elif (cx+1 == x) and (cy == y):
            pass #Just to the right, so do nothing
          elif (cx == x) and (cy != y):
            #Just move the y cursor
            self.fd.write(escape.CursorDown(cy-y))
          elif (cy == y) and (cx != x):
            self.fd.write(escape.CursorRight(x-cx))
          else:
            self.fd.write(escape.CursorSet(y+self.dy+1, x+self.dx+1))
          self.fd.write(c.format(last_attr))
          last_attr = c.attr
          cx, cy = x, y
    self.changed = {}
    if not (cx == cy == None):
      self.fd.flush()

if __name__ == '__main__':
  import sys, time
  cb = CharacterBuffer(20, 3, sys.stdout)
  cb.draw()
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
  cb.add(1, 1, "This is a test!", escape.RED)
  cb.draw()
  time.sleep(.5)
  cb.redraw()
  