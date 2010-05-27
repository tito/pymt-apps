'''
PreseMT, a presentation application
Copyright (C) 2009/2010  
    Thomas Hansen <thomas.hansen@gmail.com>
    Mathieu Virbel <tito@bankiz.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

if __name__ == '__main__':

    import sys
    from pymt import runTouchApp, getWindow

    if len(sys.argv) != 2:
        print
        print 'Usage: python start.py <filename_of_presentation.m>'
        print
        print 'To create a new presentation, just start application'
        print 'with a new filename.'
        print
        sys.exit(1)


    from app import Presemt

    m = Presemt(size=getWindow().size)
    m.load(sys.argv[1])

    runTouchApp(m)

