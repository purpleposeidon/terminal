
# -*- coding: utf-8 -*-




c_thin = "┌┐└┘"
s_thin = "│─"

c_thick = "┏┓┗┛"
s_thick = "┃━"

c_double = "╔╗╚╝"
s_double = "║═"

s_thin_dash2  = "╎╌"
s_thick_dash2 = "╏╍"
s_thin_dash3  = "┆┄"
s_thick_dash3 = "┇┅"
s_thin_dash4  = "┊┈"
s_thick_dash4 = "┋┉"

c_round = "╭╮╰╯"

j_thin = "├┤┬┴┼"
j_thick = "┣┫┳┻╋"
j_double = "╠╣╦╩╬"



class BoxedSet:
  def __repr__(self):
    r = ''
    r += self.c7+self.h*3+self.c9+'\n' #out top
    r += self.v+self.c7+self.c8+self.c9+self.v+'\n' #core top
    r += self.v+self.c4+self.c5+self.c6+self.v+'\n' #core middle
    r += self.v+self.c1+self.c2+self.c3+self.v+'\n' #core top
    r += self.c1+self.h*3+self.c3
    return r
    
  def __init__(self, corners, sides, join):
    self.corners = corners
    self.ul = self.c7 = self.nw = corners[0]
    self.ur = self.c9 = self.ne = corners[1]
    self.ll = self.c1 = self.sw = corners[2]
    self.lr = self.c3 = self.se = corners[3]
    self.sides = sides
    self.v  = self.vertical = sides[0]
    self.h  = self.horizontal = sides[1]
    self.join = join
    self.vr = self.c4 = join[0]
    self.vl = self.c6 = join[1]
    self.hd = self.c8 = join[2]
    self.hu = self.c2 = join[3]
    self.center = self.c5 = join[4]

thin = BoxedSet(c_thin, s_thin, j_thin)
thin.dash2 = BoxedSet(c_thin, s_thin_dash2, j_thin)
thin.dash3 = BoxedSet(c_thin, s_thin_dash3, j_thin)
thin.dash4 = BoxedSet(c_thin, s_thin_dash4, j_thin)
thin.dash = thin.dash2

thick = BoxedSet(c_thick, s_thick, j_thick)
thick.dash2 = BoxedSet(c_thick, s_thick_dash2, j_thick)
thick.dash3 = BoxedSet(c_thick, s_thick_dash3, j_thick)
thick.dash4 = BoxedSet(c_thick, s_thick_dash4, j_thick)
thick.dash = thick.dash2

round = BoxedSet(c_round, s_thin, j_thin)
round.dash2 = BoxedSet(c_round, s_thin_dash2, j_thin)
round.dash3 = BoxedSet(c_round, s_thin_dash3, j_thin)
round.dash4 = BoxedSet(c_round, s_thin_dash4, j_thin)
round.dash = round.dash2
double = BoxedSet(c_double, s_double, j_double)

