

import rgbcolor
import basecolor

black = rgbcolor.RgbColor(0, 0, 0) 
bob = rgbcolor.Color(fg=black, bg=black)
def test(msg=''):
  if msg:
    msg = '\n'+msg
  print(bob+"If this text is blinking, then this\nterminal can't use extended colors!"+msg+basecolor.DEFAULT)

if __name__ == '__main__':
  test()
