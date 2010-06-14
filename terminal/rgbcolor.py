
import escape
import basecolor

class GrayColor(escape.PseudoString):
  """
  Defines a gray color. Values range between 0 (almost black) to 23 (almost white).
  True black and true white can be obtained either from basecolor.BLACK and basecolor.WHITE,
  or from RgbColor(0, 0, 0) and RgbColor(5, 5, 5)
  """
  def __init__(self, val):
    self.arg = val
    assert 0 <= val <= 23
    #self.val = 216+val
    self.val = 232+val
  def __str__(self):
    return escape.CSI+"38;5;"+str(self.val)+"m"
  def __repr__(self):
    return "GrayColor({0})".format(self.arg)

class RgbColor(escape.PseudoString):
  def __init__(self, r, g, b):
    args = r, g, b
    self.args = args
    for v in args:
      assert 0 <= v <= 5
    self.val = str(16 + r*36 + g*6 + b)
  def __str__(self):
    return escape.CSI+"38;5;"+str(self.val)+"m"
  def __repr__(self):
    return "RgbColor{0}".format(self.args)

class Color(escape.PseudoString):
  def __init__(self, *attrs, **kwargs):
    fg = kwargs.get('fg', basecolor.NORMAL)
    bg = kwargs.get('bg', GrayColor(0))
    self.fg = fg
    self.bg = bg
    self.attrs = attrs
  def __str__(self):
    r = ''
    fg = "38;5;"+str(self.fg.val)+'m'
    bg = "48;5;"+str(self.bg.val)+'m'
    fg = escape.CSI+fg
    bg = escape.CSI+bg
    r += fg+bg
    for attr in self.attrs:
      r += escape.CSI+str(attr.val)+'m'
    return r
  def __repr__(self):
    return "Color({0}fg={1!r}, bg={2!r})".format(''.join(repr(_)+', ' for _ in self.attrs), self.fg, self.bg)
    #return "Color({0}, fg={1!r}, bg={2!r})".format(str(self.attrs)[1:-1], self.fg, self.bg)
  def follow(self, old):
    if not isinstance(old, Color):
      return str(self)
    r = ''
    if old.fg != self.fg:
      fg = "38;5;"+str(self.fg.val)+'m'
      fg = escape.CSI+fg
      r += fg
    if old.bg == self.bg:
      bg = "48;5;"+str(self.bg.val)+'m'
      bg = escape.CSI+bg
      r += bg
    for attr in self.attrs:
      if not (attr in old.attrs):
        r += CSI+str(attr.val)+'m'
    return r

def testbg(fg):
  import sys
  for center in range(6):
    sys.stdout.write(escape.NORMAL+'\n')
    for omask in ([1, 0, 0], [0, 1, 0], [0, 0, 1]):
      for v in range(6):
        mask = list(omask)
        imask = map(lambda x: (not x)*center, mask)
        mask = map(lambda x: x*v, mask)
        arg = map(sum, zip(mask, imask))
        sys.stdout.write(Color(fg=fg, bg=RgbColor(*arg))+''.join(str(_) for _ in arg))

def test():
  import sys
  sys.stdout.write("""
FOREGROUND COLORS
                                                      rgb
BACKGROUND COLORS
  -RED -> +RED   ||-GREEN -> +GREEN|| -BLUE -> +BLUE
rgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgbrgb""")
  for center in range(6):
    for omask in ([1, 0, 0], [0, 1, 0], [0, 0, 1]):
      for v in range(6):
        mask = list(omask)
        imask = map(lambda x: (not x)*center, mask)
        mask = map(lambda x: x*v, mask)
        arg = map(sum, zip(mask, imask))
        testbg(RgbColor(*arg))
        sys.stdout.write(escape.NORMAL+escape.CursorUp(3)+''.join(str(_) for _ in arg)+escape.CursorDown(3))
  print()
  
if __name__ == '__main__':
  try:
    test() #| less -r
  except IOError:
    pass
  except KeyboardInterrupt:
    print(escape.NORMAL)
