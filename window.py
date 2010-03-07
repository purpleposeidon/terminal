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

import coms
import keys
import escape



def exists(what):
  #Use 'which' to check that a program exists
  return not subprocess.Popen(['which', what], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()


GetSize = str(escape.AsciiCode("xS?"))
IsSize = str(escape.AsciiCode("xS=")) #"xS=40,80;"
SetBlock = str(escape.AsciiCode("xB")) #e.g, "xBi1". Form: xB[i or o][1 or 0]
InputFunc = str(escape.AsciiCode("xR")) #"xRr": sys.read;  "xRi": input(); "xRR": lineread
CloseWindow = str(escape.AsciiCode("xQ"))
NullEscape = str(escape.AsciiCode("xx"))

commands = [GetSize, IsSize, SetBlock, InputFunc, CloseWindow]


class Window:
  def is_open(self):
    try:
      self.write(NullEscape)
      return True
    except OSError:
      return False
  def make_open(self):
    if not self.is_open():
      self.create_terminal()
  def ask_size(self):
    self.write(GetSize)
  
  def close(self):
    #self.write("closing\n")
    self.write("\x1b[xQ")
    time.sleep(.01)
    self.close_files()
  
  def input_mode(self, mode):
    #r = sys.read, i = raw_input, R = Reader
    assert mode in "riR"
    self.write(InputFunc+mode)
  
  def set_blocking(self, iochoice, yesno):
    assert iochoice in 'io'
    c = str(int(yesno))
    self.write(str(SetBlock)+iochoice+c)
  
  def __del__(self):
    self.recreate = False #Window may otherwise flare up
    try:
      self.close()
    except: pass
    os.unlink(self.fifoname)
    os.unlink(self.keysname)
    
  def read(self, *args, **kwargs):
    try:
      d = self.kd.read(*args)
    except IOError:
      if kwargs.get("first"):
        self.make_open()
        d = self.read(*args, first=False)
      else:
        raise
      #return self.kd.read(*args)
    while IsSize in d:
      afore = d[:d.index(IsSize)]
      after = d[d.index(IsSize)+len(IsSize):]
      #after = after[+1:]
      #print `after`
      dim = after[:after.index(';')]
      after = after[after.index(';')+1:]
      d = afore+after
      newsize = [int(_) for _ in dim.split(',')]
      #print "Old size:", self.size, "New size:", newsize
      self.size = newsize
    return d
  def write(self, *args, **kwargs):
    try:
      for a in args:
        if not (type(a) in (str, unicode)):
          a = str(a)
        os.write(self.fd, a.encode('utf'))
      #self.flush()
    except OSError as err:
      if kwargs.get('second') or not self.recreate:
        raise
      if err.errno == 32 or err.strerror == "Broken pipe":
        self.create_terminal() #Try to re-make the terminal
        self.write(*args, second=True)
      else:
        raise

  def open_files(self):
    self.fd = os.open(self.fifoname, os.O_WRONLY)
    self.kd = self.key_out(self.keysname) #open(self.keysname)
  def close_files(self):
    os.close(self.fd)
    self.kd.close()
  def flush(self):
    self.close_files()
    self.open_files()
    #pass
    #os.fsync(self.fd)
    #except: pass
    #os.fsync(self.kd.fileno())
    #except: pass

  def create_terminal(self):
    """Runs the program to display our output"""
    DO_AND = True
    SILENCE_STDOUT = True
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
            cmd = "konsole --title {1} -e {0}"
            SILENCE_STDOUT = False #Funky bug.
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
    #tail = "cat {0} > /dev/zero 2> /dev/zero".format(self.fifoname)
    
    try:
      d = os.path.split(__file__)[0]
      if not d:
        d = os.getcwd()
      cmd_name = os.path.join(d, 'window_client.py')
    except:
      cmd_name = '`pwd`/window.py'
    tail = "{0} {1} {2}".format(cmd_name, self.fifoname, self.keysname)
    if SILENCE_STDOUT:
      tail += " > /dev/zero"
    tail += " 2> /dev/zero"
    if DO_AND:
      tail += " &"
    self.title = self.title.replace('"', '').replace("'", "\\'")
    cmd = cmd.format(tail, '"'+self.title+'"')
    if self.verbose:
      print cmd
      sys.stderr.write("\rOpening new window, if this program hangs, press Ctrl-C")
      sys.stderr.flush()
      
    r = os.system(cmd)
    self.open_files()
    coms.noblock(self.kd.fileno())
    self.ask_size()
    time.sleep(.01)
    try: self.read()
    except:
      #Try again?
      time.sleep(.05)
      try: self.read()
      except: pass
    #self.write(escape.ClearLine, '\r')
    
    if self.verbose:
      sys.stderr.write(str(escape.ClearLine)+'\r')
      sys.stderr.flush()
    
    


  def __init__(self, title="Terminal Window", verbose=True, recreate=True, key_out=coms.Input):
    """
    Creates another terminal that can be used. If the program is being called from within
    screen, it will use the command "screen" to create another screen in screen. Otherwise,
    it will try to guess the best graphical terminal to use. It returns a write-only file.

    It probably wouldn't be too difficult to be able to read input from the terminal too.
    TODO: Write cases for other graphical environments?
    TODO: Are there programs similiar to screen?
    TODO: Being able to read input would be nice
    """
    self.fifoname = tempfile.mktemp(prefix="terminal-out-")
    self.keysname = tempfile.mktemp(prefix="terminal-in-")
    os.mkfifo(self.fifoname)
    os.mkfifo(self.keysname)
    self.title = title
    self.verbose = verbose
    self.recreate = recreate
    self.fd = None
    self.kd = None
    self.key_out = key_out #coms.Input keys.stream
    self.create_terminal()
    self.write(escape.ClearScreen)
    self.size = None
    self.ask_size()
    self.write("\r")
    self.write(escape.CursorHome)




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
  winmsg = "Type stuff to be written into the other window."
  t.write(winmsg+'\n')
  import select
  inp = coms.Input()
  print winmsg
  while 1:
    orig_size = t.size
    avail = select.select([inp.fileno(), t.kd.fileno()], [], [])
    #print avail
    if inp.fileno() in avail[0]:
      try:
        i = inp.read(1)
        if i:
          t.write(i)
          #print "You wrote:", i
      except (KeyboardInterrupt, EOFError):
        break
    #try:
    if t.kd.fileno() in avail[0]:
      o = t.read()
      #print "Got:", `o`
      sys.stdout.write(o.encode('utf'))
      sys.stdout.flush()
    if t.size != orig_size:
      print "Terminal size:", t.size
    #break
