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


import os
import sys

import escape
import coms
import window

import keys
from keys import KeyState

class Reader:
  """
  A non-blocking readline implementation
  """
  def __init__(self, fd='/dev/stdin', stdout=None, prefix='', savehistory=True):
    self.lines = []
    self.lines_index = 0
    self.buffer = []
    self.index = 0
    #if isinstance(fd, coms.Input):
      #self.fd = fd
    #elif isinstance(fd, window.Window):
      #self.fd = fd.kd
      #stdout = fd
    #el
    if isinstance(fd, coms.Input): #hasattr(fd, 'read') and callable(getattr(fd, 'read')):
      self.fd = fd
    else:
      self.fd = coms.Input(fd)
    if stdout == None:
      if isinstance(fd, window.Window):
        stdout = fd
      stdout = sys.stderr
    self.stdout = stdout
    #self.i = keys.stream(self.fd)
    self.prefix = prefix
    self.savehistory = savehistory
    self.redraw()

  def redraw(self):
    val = ''.join(self.buffer).encode('utf-8')
    height, width = coms.termsize()
    #if len(val)
    self.stdout.write(str(escape.ClearLine))
    self.stdout.write('\r'+self.prefix+val)
    if self.index == len(self.buffer):
      pass
    else:
      self.stdout.write(escape.CursorLeft(len(self.buffer)-self.index))
  def __del__(self):
    self.fd.close()
    #if escape: escape.cleanup(self.i.fileno())
  def add_history(self, buff):
    b = ''.join(buff)
    if b:
      if b not in self.lines:
        self.lines.append(b)
      else:
        del self.lines[self.lines.index(b)]
        self.lines.append(buff)
  def readline(self):
    """Returns:
      None if enter wasn't pressed
      A str containing the buffer if it was
    """
    escape_sequence = []
    c = ''
    
    #while 1:
      #try:
        #c = next(self.i)
        #if c == '':
          #break
      #except StopIteration:
        #break
    #if 1:
    for c in keys.get_key(self.fd):
      if c == KeyState('LEFT'):
        self.index = max(0, self.index-1)
        self.redraw()
      elif c == KeyState('RIGHT'):
        self.index = min(len(self.buffer), self.index+1)
        self.redraw()
      elif c == KeyState("RIGHT", ctrl=True): #Ctrl-left
        self.index -= 1
        while self.index > 0 and self.buffer[self.index] in ' ':
          self.index -= 1
        while self.index > 0 and self.buffer[self.index] not in ' ':
          self.index -= 1
        self.redraw()
      elif c == KeyState("LEFT", ctrl=True): #Ctrl-right
        l = len(self.buffer)
        while self.index < l and self.buffer[self.index] in ' ':
          self.index += 1
        while self.index < l and self.buffer[self.index] not in ' ':
          self.index += 1
        self.redraw()
      elif c == 'Home':
        self.stdout.write(escape.CursorLeft(self.index))
        self.index = 0
      elif c == 'End':
        self.index = len(self.buffer)
        self.redraw()
      elif c == 'Up' and self.lines_index >= 0:
        self.add_history(self.buffer)
        self.lines_index = max(0, self.lines_index - 1)
        try:
          self.buffer = list(self.lines[self.lines_index])
        except:
          if self.lines: self.buffer = self.lines[-1]
        self.index = len(self.buffer)
        self.redraw()
      elif c == 'Down':
        if self.lines_index < len(self.lines) - 1:
          self.add_history(self.buffer)
          self.lines_index += 1
          self.buffer = list(self.lines[self.lines_index])
        else:
          self.buffer = []
        self.index = len(self.buffer)
        self.redraw()
      elif c == 'Delete': #Delete
        if self.index < len(self.buffer):
          self.buffer.pop(self.index)
          self.redraw()
      elif c == 'Enter':
        r = ''.join(self.buffer)
        self.add_history(self.buffer)
        self.buffer = []
        self.lines_index = len(self.lines)
        self.index = 0
        return r
      elif c == KeyState("D", ctrl=True): #^D
        raise EOFError
      elif c == "Backspace": #^? == backspace
        try:
          self.index -= 1
          self.index = max(0, self.index)
          self.buffer.pop(self.index)
        except: pass
        self.redraw()
      elif c == KeyState("W", ctrl=True): #^W == delete word
        word_breaks = ' ._[]'
        if self.buffer:
          self.index = min(self.index, len(self.buffer))
          while self.index: # and self.index <= len(self.buffer):
            self.index -= 1
            try:
              self.buffer.pop(self.index)
            except:
              print "Total failure:"
              print self.buffer, self.index
            if self.index == 0:
              break
            if self.buffer[self.index-1] in word_breaks:
              break
          self.redraw()
      elif c == KeyState("L", ctrl=True): #^L == Redraw
        self.redraw()
      elif c.single:
        c = c.character
        if c == "\t":
          #Replaces tabs with spaces, because I suck.
          tab_len = 4
          c = ' '*tab_len
          for _ in c:
            self.buffer.insert(self.index, _)
            self.index += 1
        else:
          self.buffer.insert(self.index, c)
          self.index += len(c)
        if self.index == len(self.buffer):
          self.stdout.write(c.encode('utf-8'))
          self.stdout.flush()
        else:
          self.redraw()



def test():
  #Could be better-implemented
  import time
  r = Reader()
  print "This shoddy test doesn't bother with select(); it should.\n"
  while 1:
    try: c = r.readline()
    except EOFError: break
    except KeyboardInterrupt: break
    if c:
      print
      print "Got:", `c`
      if c.strip() == 'exit':
        break
      print
    else:
      print escape.CursorUp, escape.CursorReturn, time.time()
    r.redraw()
    time.sleep(.01)

if __name__ == '__main__':
  test()
