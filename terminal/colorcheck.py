

import sys


import rgbcolor
import basecolor

"""
Print a friendly and hopefully invisible message to alert the user about lack of extended colors.
"""

black = rgbcolor.RgbColor(0, 0, 0) 
hidden = rgbcolor.Color(fg=black, bg=black)

base_message = hidden+"If this text is blinking, then this\n\rterminal can't use extended colors!\n\r%s"+basecolor.DEFAULT

def test(fd=None, msg=''):
  if not fd:
    fd = sys.stderr
  fd.write(base_message % msg)
  fd.flush()

if __name__ == '__main__':
  test()
