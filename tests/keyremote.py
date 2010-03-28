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

"""
An implementation of lineread for child windows
"""
import select

import terminal.window
import terminal.keys

w = terminal.window.Window("Remote key obtainer")
select.select([w], [],[])
for key in terminal.keys.stream(w):
  if key:
    print key
  select.select([w], [],[])

