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
  """Use 'which' to check that a program exists"""
  return not subprocess.Popen(['which', what], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()

#Special escape sequences that are shared with the client terminal
GetSize = str(escape.AsciiCode("XS?"))
IsSize = str(escape.AsciiCode("XS=")) #"xS=40,80;"
SetBlock = str(escape.AsciiCode("XB")) #e.g, "xBi1". Form: xB[i or o][1 or 0]
InputFunc = str(escape.AsciiCode("XR")) #"xRr": sys.read;  "xRi": input(); "xRR": lineread
CloseWindow = str(escape.AsciiCode("XQ"))
NullEscape = '\00' #str(escape.AsciiCode("Xx"))



class Window:
  def __init__(self, title="Terminal Window", verbose=True, recreate=True, key_out=coms.Input, tmp_file_prefix="terminal"):
    """
    Creates a new terminal window, accessible with a file-like object.
    The terminal is created using FIFO's and window_client.py
      TODO: Write cases for other environments

    ``title'' is passed to the created terminal in its' arguments.
    ``verbose'' controls whether or not an informative message is written as the window is created.
      (It clears the line the cursor is on, so you may wish to disable it)
    If the terminal should ``recreate'', then, if it is closed, it will re-open itself whenver flushed or written to.
      (But not when read...)
    ``key_out'' is a function that takes a file name pointing to the keys from the terminal. It must return a file-like object.
    ``tmp_file_prefix'' is pre-pended to the FIFO files.
    """
    self.title = title
    self.verbose = verbose
    self.recreate = recreate
    self.key_out = key_out #coms.Input keys.stream

    self.fifoname = tempfile.mktemp(prefix=tmp_file_prefix+"-out-")
    self.keysname = tempfile.mktemp(prefix=tmp_file_prefix+"-in-")
    os.mkfifo(self.fifoname)
    os.mkfifo(self.keysname)

    self.fd = None
    self.kd = None


    self.config_string = "{0}{1}{2}\r".format(escape.ClearScreen, escape.CursorHome, GetSize)
    self.size = None

    self.create_terminal()
  
  def config(self, val):
    """
    ``val'' is written to the terminal. If the terminal is closed and re-created, the configuration string will be re-written while it is be re-created.
    If you need to use things like set_blocking, you can do:
      window.config(window.set_blocking('i', True))
    """
    self.config_string += val
    #print 'configing with', `val`
    self.write(val)
  
  def is_open(self):
    """Returns if the terminal is open, or no."""
    try:
      os.write(self.fd.fileno(), NullEscape)
      return True
    except OSError as err:
      if err.args[0] == 32: #Borked pipe
        return False
      raise
  
  def make_open(self):
    """Opens the window if needed"""
    if not self.is_open():
      self.create_terminal()
  
  def close(self):
    """Closes the windows and FIFOs"""
    #self.write("closing\n")
    ###self.write("\x1b[xQ")
    self.write(CloseWindow)
    #self.flush()
    time.sleep(.01)
    self.close_files()
  
  def ask_size(self):
    """
    Sends the escape sequence to the terminal to ask for the window size.
    However, the size won't be updated until this class has read() the terminal's response.
    Can be used with config()
    """
    self.write(GetSize)
    return GetSize
  
  def input_mode(self, mode):
    """input_mode([r, i, R])
    Tells the terminal how to get input.
      r: sys.read
      i: raw_input
      R: input.Reader
    If using 'i' (raw_input), echo is enabled. In all other cases, it is disabled.
    Can be used with config()
    """
    val = InputFunc+mode
    self.write(val)
    return val
  
  def set_blocking(self, iochoice, yesno):
    """
    set_blocking("o"utput or "i"nput, will_block)
    Can be used with config()
    """
    assert iochoice[0] in 'io'
    c = str(int(yesno))
    val = str(SetBlock)+iochoice[0]+c
    self.write(val)
    return val
  
  def __del__(self):
    """
    Permamently closes the terminal, and destroys FIFO resources.
    """
    self.recreate = False #Window may otherwise flare up
    try: self.close()
    except: pass
    try: os.unlink(self.fifoname)
    except: pass
    try: os.unlink(self.keysname)
    except: pass

  def read(self, *args, **kwargs):
    """
    read([size]). Reads size bytes. It is typically non-blocking.
    If there is no data to be had, it returns an empty string.
    """
    try:
      d = self.kd.read(*args)
      if d == '':
        raise IOError(11, "Resource temporarily unavailable (Terminal window closed)")
    except IOError as err:
      if err.args[0] == 11: #Resource temporarily unavailable
        #The pipe is closed
        if kwargs.get("second"):
          raise
        else:
          if self.recreate:
            self.create_terminal()
            return '' #Bah!
            """
            self.flush()
            for _ in range(10):
              try:
                return self.read(*args, second=True)
              except:
                print 'uhgh, waiting a', _
                time.sleep(.01*_)
            """
          else:
            raise
    
    while IsSize in d:
      afore = d[:d.index(IsSize)]
      after = d[d.index(IsSize)+len(IsSize):]
      dim = after[:after.index(';')]
      after = after[after.index(';')+1:]
      d = afore+after
      newsize = [int(_) for _ in dim.split(',')]
      self.size = newsize
    
    return d
  
  def write(self, *args, **kwargs):
    """
    Writes args to the file. It converts to unicode. The args don't have to be strings.
    (kwargs is internally used)
    """
    try:
      for a in args:
        if not (type(a) in (str, unicode)):
          a = str(a)
        self.fd.write(a.encode('utf'))
      self.flush()
    except OSError as err:
      if kwargs.get('second') or not self.recreate:
        raise
      if (err.errno == 32) or (err.errno == 9):
        self.create_terminal() #Try to re-make the terminal
        self.write(*args, second=True)
      else:
        raise
  
  def open_files(self):
    """Opens up our coms FIFO's"""
    self.fd = open(self.fifoname, 'w')
    self.kd = self.key_out(self.keysname) #open(self.keysname)
  
  def close_files(self):
    """Close our end of the coms FIFO's"""
    self.fd.close()
    self.kd.close()
  
  def fileno(self):
    """Returns the file number of the keyboard input"""
    return self.kd.fileno()
  
  def flush(self):
    """
    Flushes output to terminal. (It might not really be necessary)
    As a side effect, it will re-create the terminal if requested.
    """
    try:
      self.fd.flush()
    except IOError as e:
      if e.args[0] == 32: #borken pipe
        if self.recreate:
          self.create_terminal()
  
  def create_terminal(self):
    """Creates a new terminal. Takes into consideration environment variables to pick the best terminal, and also has to determine the command-line argument.
      TODO XXX Use popen
    """
    self.title = self.title.replace('"', '').replace("'", "\\'")
    DO_AND = True
    SILENCE_STDOUT = True
    if "TERM" in os.environ:
      t = os.environ["TERM"]

      if t == 'screen':
        if not exists("screen"):
          raise SystemExit("$TERM is screen, yet the program 'screen' could not be found")
        #cmd = "screen -t {1} {0}"
        cmd = ["screen", "-t", self.title]
        DO_AND = False
      elif "DISPLAY" in os.environ:
        #cmd = "x-terminal-emulator -T {1} -e {0}"
        cmd = ["x-terminal-emulator", "-T", self.title, '-e']
        if "DESKTOP_SESSION" in os.environ:
          ds = os.environ["DESKTOP_SESSION"].lower()
          if 'kde' in ds and exists("konsole"):
            #cmd = "konsole --title {1} -e {0}"
            cmd = ["konsole", "--title", self.title, "-e"]
            SILENCE_STDOUT = False #Funky bug.
          elif 'gnome' in ds and exists("gnome-terminal"):
            #cmd = "gnome-terminal -t {1} --execute {0}"
            cmd = ['gnome-terminal', '-t', self.title, '--execute']
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
    #tail = "{0} {1} {2}".format(cmd_name, self.fifoname, self.keysname)
    tail = [cmd_name, self.fifoname, self.keysname]
    #if SILENCE_STDOUT:
      #tail += " > /dev/zero"
    #tail += " 2> /dev/zero"
    #if DO_AND:
      #tail += " &"
    
    #cmd = cmd.format(tail, '"'+self.title+'"')
    cmd = cmd + tail
    if self.verbose:
      #print cmd
      sys.stderr.write("\rOpening new window, if this program hangs, press Ctrl-C")
      sys.stderr.flush()
      
    
    if SILENCE_STDOUT:
      r = subprocess.Popen(cmd, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
    else:
      r = subprocess.Popen(cmd, stderr=open('/dev/null', 'w'))
    if not DO_AND:
      r.wait()
    self.open_files()
    coms.noblock(self.kd.fileno())
    self.write(self.config_string)
    self.flush()
    time.sleep(.01)
    #Read to get the terminal size
    try: self.read()
    except:
      #Try again?
      time.sleep(.05)
      try:
        self.read()
      finally:
        if not self.size:
          sys.stderr.write("Unable to get window size!\n")

    if self.verbose:
      sys.stderr.write(str(escape.ClearLine)+'\r')
      sys.stderr.flush()
    




def run_with_windowing():
  """
  If it seems that there is no windowing capability, then try to re-run this program with windowing.
  """
  in_screen = "TERM" in os.environ and 'screen' in os.environ["TERM"]
  in_x = "DISPLAY" in os.environ and os.environ["DISPLAY"]
  if not(in_screen or in_x):
    if exists("screen"):
      subprocess.call(["screen", "python"]+sys.argv)
      raise SystemExit
      #recommand = sys.argv[0]
      #for c in sys.argv[1:]:
      #  recommand += ' ' + c
      #os.system("screen python {0}".format(recommand))
    else:
      raise SystemExit("Can not continue. You must either run this program with $DISPLAY set, or you must have screen installed.")



if __name__ == '__main__':
  #A test
  t = Window("Terminal Library Test Window", recreate=False)
  winmsg = "Type stuff to be written into the other window."
  t.config(winmsg+'\n')
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
