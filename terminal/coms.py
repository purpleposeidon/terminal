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
import fcntl
import atexit
import codecs
import select
import struct
import termios


"""
DISABLE_FLOWCONTROL is enabled by default. With this, the program can catch ^S and ^Q.
DISABLE_TERM_SIG is *disabled* by default. You'd better be a fabulous programmer if you turn this on; otherwise the user won't be able to make your program to quit with ^C or whatever.

Default settings:
  Non-blocking
  Flow control disabled
  Interrupts enabled
  No echo AND Character-at-a-time

To block:
  coms.Input(blocking=True)
Enable flow control:
  coms.DISABLE_FLOWCONTROL = False
  coms.apply_ctrl_settings(fd)
Disable interrupts:
  coms.DISABLE_TERM_SIG = True
  coms.apply_ctrl_settings(fd)
Echo AND line-buffered mode:
  coms.yesecho(fd)

"""

DISABLE_FLOWCONTROL = True
DISABLE_TERM_SIG = False


RESET_STDIN = False



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
    
    self.orig_flags = None
    
    
    self.flush = self.fd.flush
    self.fileno = self.fd.fileno
    self.setblocking(blocking)
    self.read = self.fd.read

  def setblocking(self, blocking=False):
    #Note: You may wish to call this after SIGCONT
    self.blocking = blocking
    if blocking and self.orig_flags:
      cleanup(self.orig_flags, self.fileno())
    else:
      self.orig_flags = setup(self.fileno())
  
  def close(self):
    self.setblocking(True)
    self.fd.close()

  def wait(self, timeout=None):
    if not self.blocking:
      yesblock(self.fd.fileno())
    wait(self.fd, timeout=timeout)
    if not self.blocking:
      noblock(self.fd.fileno())


def termsize(default=(25, 80), fd=None, no_environ=False):
  """ Returns the (height, width) of the terminal.
  
  Stolen from somewhere.
  
  If there is a LINES and COLUMNS defined, then that is returned. (This can be overridden with
  no_environ)
  If fd is not given, the default file descriptor (STDIN/STDOUT/STDERR, determined at import time)
  is queried for the window size. If that fails, the default is returned."""
  if fd is None:
    global __fd
    fd = __fd
  try:
    if no_environ: raise KeyError
    #These are only very rarely defined.
    l, w = default
    l = int(os.environ["LINES"])
    w = int(os.environ["COLUMNS"])
    return l, w
  except KeyError:
    try:
      f = fcntl.ioctl(fd, termios.TIOCGWINSZ, "\x00"*8)
      return struct.unpack("hhhh", f)[0:2]
    except IOError: #bad file descriptor
      if default:
        return default
      raise

@atexit.register
def repair_terminal():
  """Restore terminal to shell mode"""
  global RESET_STDIN, ORIG_STDIN_FLAGS, __fd
  if RESET_STDIN:
    cleanup(ORIG_STDIN_FLAGS, __fd)
    RESET_STDIN = False

#stolen termios voodoo code is stolen magic voodoo.
#I've quite forgotten where it comes from.
#But these are completely changed from what they were originally anyways

def cleanup(old_term_flags, fd):
  """Return terminal to original state. Run like 
  cleanup(*setup())"""
  oldterm, oldflags = old_term_flags
  try:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
  except:
    pass

def yesecho(fd):
  """Turns on echoing of typed characters."""
  try:
    oldterm = termios.tcgetattr(fd)
    newattr = oldterm[:]
    newattr[3] = newattr[3] & ~termios.ICANON | termios.ECHO #& ~termios.IXOFF #| termios.ISIG
    #newattr[0] |= (termios.IXOFF | termios.IXON)
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
  except:
    #It's likely that fd isn't a tty, or something?
    pass
  return oldterm

def noecho(fd):
  """Disables echoing of typed characters."""
  try:
    oldterm = termios.tcgetattr(fd)
    newattr = oldterm[:]
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO #& ~termios.IXOFF #& ~termios.ISIG
    apply_ctrl_settings(fd)
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    return oldterm
  except:
    #It's likely that fd isn't a tty, or something?
    pass

def apply_ctrl_settings(fd):
  """
  Disables the uffects of some control keys.
  """
  oldterm = termios.tcgetattr(fd)
  newattr = oldterm[:]
  if DISABLE_FLOWCONTROL:
    newattr[0] &= ~(termios.IXOFF | termios.IXON)
  else:
    newattr[0] |= (termios.IXOFF | termios.IXON)
  if DISABLE_TERM_SIG:
    newattr[3] &= ~termios.ISIG
  else:
    newattr[3] |= termios.ISIG
  termios.tcsetattr(fd, termios.TCSANOW, newattr)

def noblock(fd):
  """
  Sets blocking mode for a file. If no data is available, then don't wait while reading.
  """
  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
  return oldflags

def yesblock(fd):
  """
  Turns on blocking mode.
  """
  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags & ~os.O_NONBLOCK)
  return oldflags

def setup(fd):
  """turns off echo, and puts the terminal into non-blocking mode.
  Returns a tuple of flags that should be used with cleanup()
  """
  oldterm = noecho(fd)
  oldflags = noblock(fd)
  if fd == 0:
    global RESET_STDIN
    RESET_STDIN = True
  return oldterm, oldflags

def wait(fd, timeout=None):
  """Wait for fd to become readable. Turns on blocking."""
  if type(fd) != int:
    fd = fd.fileno()
  yesblock(fd)
  select.select([fd], [], [], timeout)


def find_tty():
  """
  Picks the best file to use for doing fcntl with.
  """
  for fd in (sys.stdin, sys.stdout, sys.stderr):
    if fd.isatty():
      fd = fd.fileno()
      return fd

#Try to get a tty
__fd = find_tty()
__oldflags = fcntl.fcntl(__fd, fcntl.F_GETFL)
try:
  __oldterm = termios.tcgetattr(__fd)
except termios.error:
  __oldterm = None
ORIG_STDIN_FLAGS = __oldterm, __oldflags

def test():
  print("Reverses the case of the text you write")
  print("Close with ^C")
  f = Input()
  while 1:
    c = None
    select.select([f], [],[])
    try:
      c = f.read(1)
    except IOError:
      continue
    except KeyboardInterrupt:
      break
    except:
      raise
    if c:
      if c.upper() == c:
        c = c.lower()
      else:
        c = c.upper()
      sys.stdout.write(c)
      sys.stdout.flush()

if __name__ == '__main__':
  test()

