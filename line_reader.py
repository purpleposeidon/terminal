#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
import terminal


class Reader:
  def __init__(self, prefix=''):
    self.lines = []
    self.lines_index = 0
    self.buffer = []
    self.index = 0
    #self.i = os.open("/dev/stdin", os.O_RDONLY | os.O_NONBLOCK)
    self.i = codecs.open("/dev/stdin", encoding='utf-8')
    self.prefix = prefix
    terminal.term_setup(self.i.fileno())
    self.redraw()

  def redraw(self):
    val = ''.join(self.buffer).encode('utf-8')
    height, width = terminal.termsize()
    #if len(val)
    sys.stderr.write(str(terminal.ClearLine))
    sys.stderr.write('\r'+self.prefix+val)
    if self.index == len(self.buffer):
      pass
    else:
      sys.stderr.write(terminal.CursorLeft(len(self.buffer)-self.index))
  def __del__(self):
    terminal.cleanup(self.i.fileno())
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
    A str containing the buffer if it was..."""
    escape_sequence = []
    c = ''
    while 1:
      try:
        #c = os.read(self.i, 1)
        c = self.i.read(1)
        if c == '':
          break
        #print self.i, self.buffer
        #print '\r', terminal.ClearLine, repr(c)
        #self.redraw()
      except IOError:
        break
      if c == terminal.ESC:
        escape_sequence.append(c)
      elif escape_sequence:
        escape_sequence.append(c)
        e = ''.join(escape_sequence)
        if str(terminal.CursorLeft) in e:
          self.index = max(0, self.index-1)
          self.redraw()
        elif str(terminal.CursorRight) in e:
          self.index = min(len(self.buffer), self.index+1)
          self.redraw()
        elif '\x1b[1;5D' in e: #Ctrl-left
          self.index -= 1
          while self.index > 0 and self.buffer[self.index] in ' ':
            self.index -= 1
          while self.index > 0 and self.buffer[self.index] not in ' ':
            self.index -= 1
          self.redraw()
        elif '\x1b[1;5C' in e: #Ctrl-right
          l = len(self.buffer)
          while self.index < l and self.buffer[self.index] in ' ':
            self.index += 1
          while self.index < l and self.buffer[self.index] not in ' ':
            self.index += 1
          self.redraw()
        elif str(terminal.CursorHome) in e or e == terminal.CSI+'1~':
          sys.stderr.write(terminal.CursorLeft(self.index))
          self.index = 0
        elif str(terminal.CursorEnd) in e or e == terminal.CSI+'4~':
          self.index = len(self.buffer)
          self.redraw()
        elif str(terminal.CursorUp) in e and self.lines_index >= 0:
          self.add_history(self.buffer)
          self.lines_index -= 1
          if self.lines_index == -1:
            self.lines_index = 0
          try:
            self.buffer = list(self.lines[self.lines_index])
          except:
            if self.lines: self.buffer = self.lines[-1]
          self.index = len(self.buffer)
          self.redraw()
        elif str(terminal.CursorDown) in e:
          if self.lines_index < len(self.lines) - 1:
            self.add_history(self.buffer)
            self.lines_index += 1
            self.buffer = list(self.lines[self.lines_index])
          else:
            self.buffer = []
          self.index = len(self.buffer)
          self.redraw()
        elif e == terminal.CSI+'3~': #Delete
          if self.index < len(self.buffer):
            self.buffer.pop(self.index)
            self.redraw()
        else:
          if self.buffer == ['?']:
            print
            print escape_sequence
            print
            self.redraw()
          continue
        escape_sequence = []
      elif c == '\n':
        r = ''.join(self.buffer)
        self.add_history(self.buffer)
        self.buffer = []
        self.lines_index = len(self.lines)
        self.index = 0
        return r
      elif c == '\x04': #^D
        raise EOFError
      elif c == '\x7f': #^? == backspace
        try:
          self.index -= 1
          self.index = max(0, self.index)
          self.buffer.pop(self.index)
        except: pass
        self.redraw()
      elif c == '\x17': #^W == delete word
        word_breaks = ' ._[]'
        if self.buffer:
          while self.index:
            self.index -= 1
            self.buffer.pop(self.index)
            if self.index == 0:
              break
            if self.buffer[self.index-1] in word_breaks:
              break
          self.redraw()
      elif c == '\x0c': #^L == Redraw
        self.redraw()
      else:
        if c == '\t':
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
          sys.stderr.write(c.encode('utf-8'))
          sys.stderr.flush()
        else:
          self.redraw()
    if c:
      return False #bool(False) == bool(None), however, False means something happened



if __name__ == '__main__':
  r = Reader()
  while 1:
    c = r.readline()
    if c:
      print "\nGOT:", repr(c)
      if c.strip() == 'exit':
        break
