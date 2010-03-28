

import escape
AttrNum = escape.AttrNum
BRIGHT = escape.BRIGHT
NORMAL = escape.NORMAL
CSI = escape.CSI

#Base colors
_DEFAULT = AttrNum(0, name="_DEFAULT") #Also known as "NORMAL"
_BLACK = AttrNum(30, name="_BLACK")
_RED = AttrNum(31, name="_RED")
_GREEN = AttrNum(32, name="_GREEN")
_BROWN = AttrNum(33, name="_BROWN") #"yellow"
_BLUE = AttrNum(34, name="_BLUE")
_PURPLE = AttrNum(35, name="_PURPLE") #"magenta"
_CYAN = AttrNum(36, name="_CYAN")
_GRAY = AttrNum(37, name="_GRAY") #"white"


class Color(escape.PseudoString):
  def __init__(self, *attrs, **kwargs):
    fg = kwargs.get('fg', _DEFAULT)
    bg = kwargs.get('bg', _BLACK)
    if isinstance(bg, Color):
      #Can't set special foregrounds to background, sadly
      bg = bg.fg
    #if isinstance(fg, Color):
    #  attrs = fg.attrs #+ attrs
    #  fg = fg.fg
    self.fg = fg
    self.bg = bg
    self.attrs = attrs
  def __str__(self):
    #XXX I bet you can do "CSI attribute; attribute; attribute m"
    r = ''
    if self.fg:
      r += str(self.fg)
      #r += CSI+str(self.fg.val)+'m'
    if self.bg:
      r += CSI+str(self.bg.derived+10)+'m'
    for attr in self.attrs:
      r += CSI+str(attr.val)+'m'
    return r
  def follow(self, old):
    if not isinstance(old, Color):
      return str(self)
    r = ''
    for attr in self.attrs:
      if not (attr in old.attrs):
        r += CSI+str(attr.val)+'m'
    if old.fg != self.fg:
      r += str(self.fg)
    if old.bg != self.bg:
      r += CSI+str(self.bg.derived+10)+'m'
    return r

  def __repr__(self):
    return repr(str(self))


#Colors with attributes
DEFAULT = Color(fg=_DEFAULT)
BLACK = Color(fg=_BLACK)
RED = Color(fg=_RED)
GREEN = Color(fg=_GREEN)
BROWN = Color(fg=_BROWN)
BLUE = Color(fg=_BLUE)
PURPLE = Color(fg=_PURPLE)
CYAN = Color(fg=_CYAN)
GRAY = Color(fg=_GRAY)

#Advanced colors (These can't be used in the background)
DARK_GRAY = Color(BRIGHT, fg=_BLACK)
WHITE = Color(BRIGHT, fg=_GRAY)
ORANGE = Color(BRIGHT, fg=_RED)
LIGHT_GREEN = Color(BRIGHT, fg=_GREEN)
LIGHT_BLUE = Color(BRIGHT, fg=_BLUE)
YELLOW = Color(BRIGHT, fg=_BROWN)
LIGHT_CYAN = Color(BRIGHT, fg=_CYAN)
PINK = Color(BRIGHT, fg=_PURPLE)

colors = {'default':DEFAULT, 'black':BLACK, 'red':RED, 'green':GREEN, 'brown':BROWN, 'blue':BLUE, 'purple':PURPLE, 'cyan':CYAN, 'gray':GRAY, 'dark gray':DARK_GRAY, 'white':WHITE, 'orange':ORANGE, 'light green':LIGHT_GREEN, 'light blue':LIGHT_BLUE, 'yellow':YELLOW, 'light cyan':LIGHT_CYAN, 'pink':PINK}

def test():
  import sys
  import escape
  for fg in colors:
    sys.stdout.write(colors[fg]+fg+NORMAL+":")
    sys.stdout.write(escape.CursorLeft(99)+escape.CursorRight(20)+'|')
    #sys.stdout.write((fg+':').ljust(20)+'|')
    for bg in colors:
      sys.stdout.write(Color(fg=colors[fg], bg=colors[bg]) + 'X')
    sys.stdout.write(NORMAL+'|\n')

if __name__ == "__main__":
  test()
