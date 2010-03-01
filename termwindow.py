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
import time
import tempfile
import subprocess

import escape

def exists(what):
  #Use 'which' to check that a program exists
  return not subprocess.Popen(['which', what], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()



class Window:
  def __del__(self):
    os.unlink(self.fifoname)
    if self.fd:
      os.close(self.fd)
  
  def write(self, *args):
    try:
      while args:
        a = args[0]
        os.write(self.fd, str(a).encode('utf'))
        args = args[1:]
    except OSError as err:
      if err.errno == 32 or err.strerror == "Broken pipe":
        self.create_terminal() #Try to re-make the terminal
        #Try to re-write everything... but don't try too hard
        for a in args:
          os.write(self.fd, bytes(str(a), 'utf8'))
      else:
        raise

  def flush(self):
    os.fsync(self.fd)
    pass

  def create_terminal(self):
    """Runs the program to display our output"""
    DO_AND = True
    if "TERM" in os.environ:
      t = os.environ["TERM"]

      if t == 'screen':
        if not exists("screen"):
          raise SystemExit("$TERM is screen, yet the program 'screen' could not be found")
        cmd = "screen -t {1} {0}"
        DO_AND = False
      elif "DISPLAY" in os.environ:
        cmd = "x-terminal-emulator -T {1} -e {0}"
        if "DESKTOP_SESSION" in os.environ:
          ds = os.environ["DESKTOP_SESSION"].lower()
          if 'kde' in ds and exists("konsole"):
            cmd = "konsole --caption {1} --title {1} -e {0}"
          elif 'gnome' in ds and exists("gnome-terminal"):
            cmd = "gnome-terminal -t {1} --execute {0}"
      else:
        if not exists("screen"):
          raise SystemExit("Can not continue. You will either need to run this program from a graphical environment, or install the program 'screen'.")
        else:
          raise SystemExit("Can not continue. You will either need to run this program from a graphical environment, or from 'screen'")
    else:
      raise SystemExit("This program requires the TERM environment variable to be defined.")
    #Another option would be try using "TERM" as the name of the shell to execute, but it would be unlikely to ever get there (And might be a little bit insecure)
    tail = "cat {0} > /dev/zero 2> /dev/zero".format(self.fifoname)
    if not exists("cat"):
      if not exists("type"):
        raise SystemExit("command 'cat' not found. What kind of person doesn't have a cat?")
    if DO_AND:
      tail += " &"
    cmd = cmd.format(tail, repr(self.title))
    if self.verbose:
      sys.stderr.write("\r If this program hangs, press Ctrl-C")
      sys.stderr.flush()
      
    r = os.system(cmd)
    self.fd = os.open(self.fifoname, os.O_WRONLY)
    #self.write(escape.ClearLine, '\r')
    
    if self.verbose:
      sys.stderr.write(str(escape.ClearLine)+'\r')
      sys.stderr.flush()
    
    


  def __init__(self, title="", verbose=True):
    """
    Creates another terminal that can be used. If the program is being called from within
    screen, it will use the command "screen" to create another screen in screen. Otherwise,
    it will try to guess the best graphical terminal to use. It returns a write-only file.

    It probably wouldn't be too difficult to be able to read input from the terminal too.
    TODO: Write cases for other graphical environments?
    TODO: Are there programs similiar to screen?
    TODO: Being able to read input would be nice
    """
    self.fifoname = tempfile.mktemp(prefix="terminal-")
    self.title = title
    self.verbose = verbose
    self.fd = None
    os.mkfifo(self.fifoname)
    self.create_terminal()




in_screen = "TERM" in os.environ and os.environ["TERM"] == 'screen'
in_x = "DISPLAY" in os.environ and os.environ["DISPLAY"]
if not(in_screen or in_x):
  if exists("screen"):
    recommand = sys.argv[0]
    for c in sys.argv[1:]:
      recommand += ' ' + c
    os.system("screen python {0}".format(recommand))
  else:
    raise SystemExit("Can not continue. You must either run this program with $DISPLAY set, or you must have screen installed.")


if __name__ == '__main__':
  t = Window("Terminal Library Test Window")
  t.write("Test!\n")
  print "Echo program!"
  while 1:
    try:
      t.write(raw_input())
    except (KeyboardInterrupt, EOFError):
      break
  
