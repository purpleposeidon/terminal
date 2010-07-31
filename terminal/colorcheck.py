

import sys


import terminal.rgbcolor
import terminal.basecolor

"""
Print a friendly and hopefully invisible message to alert the user about lack of extended colors.
"""

black = terminal.rgbcolor.RgbColor(0, 0, 0) 
hidden = terminal.rgbcolor.Color(fg=black, bg=black)

base_message = hidden+"If this text is blinking, then this\n\rterminal can't use extended colors!\n\r%s"+terminal.basecolor.DEFAULT

def test(fd=None, msg=''):
  if not fd:
    fd = sys.stderr
  fd.write(base_message % msg)
  fd.flush()

if __name__ == '__main__':
  test()
