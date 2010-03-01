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


class Character:
  #A thought: What about multi-cell items?
  def dup(self):
    """If you're going to be manipulating characters (or colors) on an individual basis, you'll need to duplicate them. Otherwise, all of them will change!"""
    return Character(self.symbol, self.ascii, self.color)
  def __init__(self, symbol, ascii=None, color=GRAY, name='(No name)', flavor='(No flavor)'):
    #XXX: What about animated stuff?
    self.symbol = symbol
    self.color = color
    self.name = name
    self.description = flavor
    if not ascii:
      if ord(symbol) < 255:
        self.ascii = symbol
      else:
        self.ascii = '?'
    else:
      self.ascii = ascii

  def __str__(self):
    return "%s%s" % (self.color, self.symbol)

empty_char = Character(' ', ascii=' ')

class ScreenBuffer:
  def __init__(self):
    self.buff = {}
  def __setitem__(self, add, val):
    self.buff[add] = val
  def __getitem__(self, pos):
    return self.buff.get(pos, empty_char)
  def diff_char(self, old, pos):
    c = self[pos]
    b = old[pos]
    return (c.symbol == b.symbol) and (c.color == b.color)
  def draw(self, fd, old, width, height, draw_count=0):
    #if draw_count: return
    fd.write(CursorHome)
    con = ''
    old_attr = None
    for y in range(0, width):
      l = ''
      for x in range(0, height):
        p = (x, y)
        c = self[p]
        if c.color == old_attr:
          l += c.symbol
        else:
          l += str(c)
          old_attr = c.color

      #fd.write(l+'\n\r')
      con += l + '\n\r'
    fd.write(con)

    return
    for y in range(0, width):
      #Build list of what needs to be redrawn
      needs_refresh = []
      for x in range(0, height):
        if self.diff_char(old, (x, y)):
          needs_refresh.append(( x, self[(x, y)] ))

      #Now, redraw.
      #Moving costs CSI+2 char, reprinting costs CSI+4 char if the attr has changed, only 1 char if the attr is the same as the one to the left.
      # TODO This could be made more efficient by checking if the distance to move is less than 3 and all of those symbols are the same
      oldattr = None
      while needs_refresh:
        x, c = needs_refresh.pop(0)
        if c.color == oldattr:
          fd.write(c.symbol)
        else:
          oldattr = c.color
          fd.write(str(oldattr)); fd.write(c.symbol)
        if len(needs_refresh) > 1:
          dx = (needs_refresh[1][0] - x) - 1
          if dx > 0:
            fd.write(CursorRight(dx))
      fd.write('\r\n')
