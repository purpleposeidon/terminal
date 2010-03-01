#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import fcntl
import atexit
import codecs
import struct
import termios


RESET_STDIN = False

def termsize(default=(25, 80)):
  """ Returns the (height, width) of the terminal. Stolen from somewhere."""
  try:
    #These are only very rarely defined.
    l, w = default
    try: l = int(os.environ["LINES"])
    except: pass
    try: w = int(os.environ["COLUMNS"])
    except: pass
    return l, w
  except KeyError:
    f = fcntl.ioctl(1, termios.TIOCGWINSZ, "\x00"*8)
    height, width = struct.unpack("hhhh", f)[0:2]
    if not height:
      return default
    return height, width


class Input:
  def __init__(self, file_name=None, blocking=False):
    """
    UTF-enabled non-blocking file
    """
    if file_name == None:
      file_name = '/dev/stdin'
      global RESET_STDIN
      RESET_STDIN = True
    
    self.fd = codecs.open(file_name, 'r', encoding='utf', errors='replace')
    #Do I fail as a programmer, or is it impossible to subclass codecs.StreamReader?
    
    
    self.read = self.fd.read
    self.flush = self.fd.flush
    self.fileno = self.fd.fileno
    self.setblocking(blocking)
  
  def setblocking(self, blocking=False):
    #Note: You may wish to call this after SIGCONT
    if blocking and self.orig_flags:
      cleanup(self.orig_flags, self.fileno())
    else:
      self.orig_flags = setup(self.fileno())
  
  def close(self):
    codecs.StreamReader.close(self)
    self.setblocking(True)


@atexit.register
def repair_terminal():
  #Restore terminal to shell mode
  global RESET_STDIN, ORIG_STDIN_FLAGS
  if RESET_STDIN:
    cleanup(ORIG_STDIN_FLAGS, sys.stdin.fileno())
    RESET_STDIN = False

#stolen termios voodoo code is stolen magic voodoo.
#I've quite forgotten where it comes from.

def cleanup(old_term_flags, fd):
  """Return terminal to sanity, remove plumbing"""
  oldterm, oldflags = old_term_flags
  try:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
  except:
    pass


def setup(fd):
  """Puts the terminal the way we want it. This code is also stolen.
  It turns off echo, and puts the terminal into non-blocking mode.
  Returns a tuple of flags that should be used with cleanup()
  """
  
  oldterm = termios.tcgetattr(fd)
  newattr = oldterm[:]
  try:
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
  except:
    #It's likely that fd isn't a tty, or something?
    pass
  
  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
  return oldterm, oldflags


__fd = sys.stdin.fileno()
__oldflags = fcntl.fcntl(__fd, fcntl.F_GETFL)
__oldterm = termios.tcgetattr(__fd)
ORIG_STDIN_FLAGS = __oldterm, __oldflags


if __name__ == '__main__':
  print "Reverses the case of the text you write"
  print "It also uses 100% of a core"
  f = Input()
  while 1:
    c = None
    try:
      c = f.read(1)
    except IOError:
      continue
    except KeyboardInterrupt:
      break
    except:
      break
    #except Exception as e:
      #print e.__class__.__name__
      #break
    if c:
      if c.upper() == c:
        c = c.lower()
      else:
        c = c.upper()
      sys.stdout.write(c)
      sys.stdout.flush()