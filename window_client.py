#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import select
import readline
import codecs

import escape
import coms
import window
import lineread

"""
Needed commands:
  What size is it?
  set blocking
  line mode
  Close
"""



def main(display_file, keys_file):
  print "Window not connected . . ."
  df = coms.Input(display_file)
  kf = open(keys_file, 'w')
  output = ''
  input_mode = 'r'
  line_reader = lineread.Reader()
  first = True
  while 1:
    avail = select.select([line_reader.fd, df], [], [])
    if first or (df in avail[0]):
      if not output:
        output = ''
        while 1:
          try: output += df.read(1)
          except IOError: break
      #print `output`
      output = unicode(output)
      while output:
        if output.startswith(window.GetSize):
          h, w = coms.termsize()
          kf.write(window.IsSize+str(h)+','+str(w)+';')
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
          return
        elif output.startswith(window.NullEscape):
          output = output.replace(window.NullEscape, '', 1)
        else:
          sys.stdout.write(output[0])
        output = output[1:]
          #sys.stdout.flush()
      output = ''
      sys.stdout.flush()
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

if __name__ == '__main__':
  if len(sys.argv) == 3:
    name, df, kf = sys.argv
    sys.stdout = codecs.open("/dev/stdin", 'w', 'utf')
    try:
      main(df, kf)
    except Exception as e:
      print e
      raw_input("Press enter to continue. . .")
      raise
  else:
    print "This program is used by window.py\nUsage: {0} terminaloutputfile keyinputfile".format(sys.argv[0])
    raw_input()
  