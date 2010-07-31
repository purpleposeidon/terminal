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

import sys
import codecs
import select
import signal
import readline


import terminal
from terminal import escape
from terminal import coms
from terminal import window
from terminal import lineread

"""
Needed commands:
  What size is it?
  set blocking
  line mode
  Close
"""



def say_size(w, h, kf):
  kf.write(window.IsSize+str(h)+','+str(w)+';')
  kf.flush()

def main(display_file, keys_file):
  print("Window not connected . . .")
  df = coms.Input(display_file)
  kf = open(keys_file, 'w')
  def resize_handler(*args):
    try:
      w, h = coms.termsize()
      say_size(w, h, kf)
    except:pass
  signal.signal(signal.SIGWINCH, resize_handler)
  output = ''
  input_mode = 'r'
  line_reader = lineread.Reader()
  first = True
  
  while 1:
    try:
      avail = select.select([line_reader.fd, df], [], [])
    except select.error as err:
      #print err
      #print err.args
      if err.args[0] == 4: #XXX 4? What?
        #This is alright, this happens when there's been a SIGWINCH
        continue
      raise
    wrote_output = False
    if first or (df in avail[0]):
      if not output:
        output = ''
        while 1:
          try: output += df.read(1)
          except IOError: break
      #print `output`, window.CloseWindow
      output = unicode(output)
      wrote_output = True
      while output:
        #print `window.CloseWindow`, ' --> ', `output`
        if output.startswith(window.GetSize):
          h, w = coms.termsize()
          say_size(h, w, kf)
          output = output.replace(window.GetSize, '', 1)
          kf.flush()
        elif output.startswith(window.SetBlock):
          output = output.replace(window.SetBlock, '', 1)
          i_or_o = output[0]
          mode = output[1]
          output = output[2:]
          #try:
          {'1':coms.yesblock, '0':coms.noblock}[mode]({'i':0, 'o':1}[i_or_o])
          #except: pass
        elif output.startswith(window.InputFunc):
          output = output.replace(window.InputFunc, '', 1)
          input_mode = output[0]
          if input_mode == 'R':
            coms.noecho(line_reader.fd)
            #print "Reading with Reader"
          elif input_mode == 'i':
            coms.yesecho(line_reader.fd)
            #print "Reading with raw_input"
          else:
            coms.noecho(line_reader.fd)
            #print "Reading with readline()"
          output = output[1:]
        elif output.startswith(window.CloseWindow):
          print('yes I got it okay')
          output = ''
          return
        elif output.startswith(window.NullEscape):
          output = output.replace(window.NullEscape, '', 1)
        else:
          sys.stdout.write(output[0])
          output = output[1:]
          #sys.stdout.flush()
      output = ''
      sys.stdout.flush()
    if wrote_output:
      if input_mode == 'R':
        line_reader.redraw()
    #if 1: #line_reader.fd in avail:
    if first or (line_reader.fd in avail[0]):
      #print 'get keypress'
      data = ''
      #Handle reading from keyboard
      try:
        if input_mode == 'R':
          #use linereader
          data = line_reader.readline()
          if data:
            data += '\n'
            print
        elif input_mode == 'i':
          #use input()
          data = raw_input()
          if data:
            line_reader.history.append(data)
            data += '\n'
        else:
          #use fd.read()
          data = line_reader.fd.read()
      except: pass
      if data:
        #print "You wrote:", data
        data = data.encode('utf')
        kf.write(data)
        kf.flush()
    first = False

def test():
  if len(sys.argv) == 3:
    name, df, kf = sys.argv
    sys.stdout = codecs.open("/dev/stdin", 'w', 'utf')
    try:
      main(df, kf)
    except Exception as e:
      print("Got exception:")
      print(e)
      print("Press enter to continue. . .")
      raw_input()
      raise
  else:
    print("This program is used by window.py\nUsage: {0} terminaloutputfile keyinputfile".format(sys.argv[0]))
    #raw_input()


if __name__ == '__main__':
  test()
