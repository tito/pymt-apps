'''
Vizplay, play with visualization of some openprocessing sketch
Copyright (C) 2009  Mathieu Virbel <tito@bankiz.org>

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

from __future__ import with_statement
from math import cos, sin, pi, sqrt, floor, radians
from random import random
from array import array
from pymt import *
from OpenGL.GL import *
from OpenGL.arrays import vbo
import os

# use cython extension if available
try:
    import pyximport
    pyximport.install()
    import vizfast
except ImportError:
    vizfast = None

# some facilities
ww, wh = ws = getWindow().size
w2, h2 = ww / 2., wh / 2.


def constrain(val,min,max):
    if val < min:
        return min
    if val > max:
        return max
    return val

class VizScenarioWater(MTWidget):
    title = 'Water'
    author = 'Remi'
    
    def __init__(self, **kwargs):
        super(VizScenarioWater, self).__init__(**kwargs)
        
        self.damping = 0.95 # attenuation
        self.radius = 10     # radius of the splash
        self.previousWave = 0
        self.currentWave = 1
        self.w = 300 # dimensions of the texture
        self.h = 194

        self.waves = list(0 for x in range(2 * self.w * self.h))
        
        self.render = array('B', '\x00' * self.w * self.h * 3)
        self.texture = Texture.create(self.w, self.h, format=GL_RGB)
        self.bpp=4
        self.bg = Image.load(os.path.join(os.path.dirname(__file__), 'ressource/pymt-logo.png'), keep_data=True)
        #self.bpp=3
        #self.bg = Image.load(os.path.join(os.path.dirname(__file__), 'ressource/back.jpg'), keep_data=True)
        
        #extract colour components
        self.r = list('\x00' * self.w * self.h)
        self.g = list('\x00' * self.w * self.h)
        self.b = list('\x00' * self.w * self.h)
        for y in range(0,self.h):
            for x in range(0,self.w):
                self.r[x+y*self.w] = ord(self.bg.image._data.data[(x + y*self.w)*self.bpp])
                self.g[x+y*self.w] = ord(self.bg.image._data.data[(x + y*self.w)*self.bpp+1])
                self.b[x+y*self.w] = ord(self.bg.image._data.data[(x + y*self.w)*self.bpp+2])

    def on_touch_up(self, touch):
        x = touch.x - (ww-self.w)/2
        y = touch.y - (wh-self.h)/2
        if x >= 0 and x <= self.w and y >= 0 and y <= self.h:
            self.drop(x, y)
    
    def on_touch_move(self, touch):
        x = touch.x - (ww-self.w)/2
        y = touch.y - (wh-self.h)/2
        if x >= 0 and x <= self.w and y >= 0 and y <= self.h:
            self.drop(x, y)

    def on_update(self):
        pass
    
    def drop(self,X,Y):
        X = int(X)
        Y = int(Y)
        for y in range(Y - self.radius, Y + self.radius):
            for x in range(X - self.radius, X + self.radius):
                dist = sqrt( (X - x)*(X - x) + (Y - y)*(Y - y))
                if dist < self.radius:
                    if x > 0 and x < self.w -1 and y > 0 and y < self.h -1:
                        self.waves[self.currentWave*self.w*self.h+x+y*self.w] = int ((255 - (512 * (1 - dist) / self.radius))/2);

    def draw(self):

        if vizfast:
            vizfast.waterWave(self.w, self.h, self.waves, self.currentWave,
                              self.previousWave, self.damping)
        else:
            #update the waves
            for y in range(1, self.h-1):
                for x in range(1, self.w-1):
                    self.waves[self.currentWave*self.w*self.h+x+y*self.w] = int((( 
                        self.waves[self.previousWave*self.w*self.h + x-1 +     y*self.w] + 
                        self.waves[self.previousWave*self.w*self.h + x+1 +     y*self.w] +
                        self.waves[self.previousWave*self.w*self.h + x   + (y-1)*self.w] +
                        self.waves[self.previousWave*self.w*self.h + x   + (y+1)*self.w] ) / 2 -
                        self.waves[self.currentWave*self.w*self.h  + x   +     y*self.w] ) * self.damping)
        
        #draw the image
        if vizfast:
            vizfast.waterDraw(self.w, self.h, self.waves, self.currentWave,
                          self.r, self.g, self.b, self.render)
        else:
            for y in range(1, self.h-1):
                for x in range(1, self.w-1):
                    
                    Xoffset = (self.waves[self.currentWave*self.w*self.h +x-1 +     y*self.w] - self.waves[self.currentWave*self.w*self.h + x+1 +     y*self.w]) / 32
                    Yoffset = (self.waves[self.currentWave*self.w*self.h +x   + (y-1)*self.w] - self.waves[self.currentWave*self.w*self.h + x   + (y+1)*self.w]) / 32
                    
                    xnew = x + Xoffset
                    ynew = y + Yoffset
                    
                    xnew = constrain(xnew, 0, self.w-1)
                    ynew = constrain(ynew, 0, self.h-1)
                    
                    shading = (Xoffset - Yoffset) / 2
                    
                    r = self.r[xnew + ynew*self.w] + shading
                    g = self.g[xnew + ynew*self.w] + shading
                    b = self.b[xnew + ynew*self.w] + shading
                    r = constrain(r, 0, 255)
                    g = constrain(g, 0, 255)
                    b = constrain(b, 0, 255)
                    
                    self.render[(x + y*self.w)*3    ] = r
                    self.render[(x + y*self.w)*3 + 1] = g
                    self.render[(x + y*self.w)*3 + 2] = b


        self.texture.blit_buffer(self.render.tostring())
        set_color(1)
        #zoomed
        #drawTexturedRectangle(texture=self.texture, size=(ww/2,wh/2), pos=( (ww-ww/2)/2,(wh-wh/2)/2))
        drawTexturedRectangle(texture=self.texture, size=(self.w,self.h), pos=( (ww-self.w)/2,(wh-self.h)/2))
                
        #swap the two waves
        self.previousWave = 1 - self.previousWave
        self.currentWave  = 1 - self.currentWave


#
# Inspiration from Jonathan Chemia
# http://www.openprocessing.org/visuals/?visualID=8857
#

class Blob(object):
    def __init__(self, x=None, y=None, r=None, dx=None, dy=None):
        super(Blob, self).__init__()
        self.r = r or max(20, random() * 100)
        self.x = x or random() * (ww - 2 * self.r)
        self.y = y or random() * (wh - 2 * self.r)
        self.dx = min(dx, 20) or 10 - random() * 20
        self.dy = min(dy, 20) or 10 - random() * 20


class VizScenarioBlob(MTWidget):
    title = 'Blob'
    author = 'Jonathan Chemia'
    def __init__(self, **kwargs):
        super(VizScenarioBlob, self).__init__(**kwargs)
        self.blobs = []
        for x in xrange(5):
            self.blobs.append(Blob())

    def on_touch_up(self, touch):
        r = None
        if 'pressure' in touch.profile:
            r = touch.pressure * 50
        elif 'shape' in touch.profile:
            r = touch.shape.width * touch.shape.height
        self.blobs.append(Blob(x=touch.x, y=touch.y, r=r,
                              dx=touch.x - touch.dxpos,
                              dy=touch.y - touch.dypos))
        if len(self.blobs) > 200:
            self.blobs = self.blobs[1:]


    def on_update(self):
        dt = getFrameDt() * 2
        for x in self.blobs:
            x.x += x.dx * dt
            x.y += x.dy * dt
            if x.x + x.r > ww:
                x.dx = -x.dx
                x.x = ww - x.r
            if x.x - x.r < 0:
                x.dx = -x.dx
                x.x = x.r
            if x.y + x.r > wh:
                x.dy = -x.dy
                x.y = wh - x.r
            if x.y - x.r < 0:
                x.dy = -x.dy
                x.y = x.r

    def draw(self):
        set_color(59/255., 126/255., 197/255., .3)
        for x in self.blobs:
            drawCircle(pos=(x.x, x.y), radius=(x.r))

        x2 = None
        set_color(18/255., 178/255., 133/255., .3)
        for x in self.blobs:
            if x2:
                drawLine([x.x, x.y, x2.x, x2.y])
            x2 = x




#
# Inspiration from James Noeckel
# http://www.openprocessing.org/visuals/?visualID=8941
#

class VizScenarioTree(MTWidget):
    title = 'Advanced Vizualisation Tree'
    author = 'James Noeckel'
    def __init__(self, **kwargs):
        super(VizScenarioTree, self).__init__(**kwargs)
        self.d = pi/2.
        self.a = pi/8.
        self.z = 0
        self.l = wh/5.
        self.da = self.a
        self.dd = self.d
        self.dz = self.z
        self.dl = self.l
        self.vbo = vbo.VBO('', usage=GL_STREAM_DRAW, target=GL_ARRAY_BUFFER)

    def draw(self):
        set_color(1, 1, 1, .7)
        drawLine([ww/2., 0, ww/2., wh/6.])
        drawTree = self.drawTree
        if vizfast:
            drawTree = vizfast.drawTree
        lines = array('f')
        drawTree(lines=lines, x=ww/2., y=wh/6., l=self.l,
                 d=self.d, a=self.a, z=self.z, depth=0)
        self.vbo.set_array(lines.tostring())
        with self.vbo:
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, None)
            glDrawArrays(GL_LINES, 0, len(self.vbo))
            glDisableClientState(GL_VERTEX_ARRAY)

        #drawPolygon(lines, style=GL_LINES)

    def drawTree(self, lines, x, y, l, d, a, z, depth):
        # x,y = pos
        # l = length
        # d = direction (radian)
        # a = angle (radian))
        # depth = depth recursivity
        if depth >= 14:
            return

        f = 1 / (1 + float(depth) / 2.)
        dx = x + l * cos(d)
        dy = y + l * sin(d)
        lines.extend([x, y, dx, dy])
        l /= 1.4
        depth += 1

        self.drawTree(lines, dx, dy, l, d-a+z, a, z, depth)
        self.drawTree(lines, dx, dy, l, d+a+z, a, z, depth)

    def on_touch_move(self, touch):
        self.da = touch.sy * pi
        self.dz = touch.sx * 10

    def on_update(self):
        da = self.da - self.a
        dd = self.dd - self.d
        dz = self.dz - self.z
        dl = self.dl - self.l
        self.a += da / 10.
        self.d += dd / 10.
        self.z += dz / 10.
        self.l += dl / 10.


#
# Inspiration from Kyle McDonald
# http://www.openprocessing.org/visuals/?visualID=1182
#

class Cell(object):
    def __init__(self, x=None, y=None, s=None, c=None):
        super(Cell, self).__init__()
        self.x = x or random() * (ww - 2 * self.r)
        self.y = y or random() * (wh - 2 * self.r)
        self.s = 0
        self.c = 0

class VizScenarioEmpathy(MTWidget):
    title = 'Empathy'
    author = 'Kyle McDonald'
    bd = 37     # base line length
    sp = .004   # rotation speed step
    sl = .97    # slow down rate
    def __init__(self):
        super(VizScenarioEmpathy, self).__init__()
        cells = []
        n = 2500.
        for i in xrange(int(n)):
            a = i + random() * (pi / 9.)
            r = (i / n) * (ww / 2.5) * (((n-i) / n) * 3.3) + (random() * 6 - 3) + 3
            cells.append(Cell(r * cos(a) + w2, r * sin(a) + h2))
        self.cells = cells
        self.dx = self.dy = 0
        self.odx = self.ody = 0

    def det(self, x1, y1, x2, y2, x3, y3):
        return (x2-x1) * (y3-y1) - (x3-x1) * (y2-y1)

    def on_touch_move(self, touch):
        self.dx, self.dy = touch.x, touch.y
        self.odx, self.ody = touch.dxpos, touch.dypos

    def on_update(self):
        if not self.odx and not self.ody:
            return
        det = self.det
        sp, sl = self.sp, self.sl
        odx, ody, dx, dy = self.odx, self.ody, self.dx, self.dy
        for cell in self.cells:
            x, y = cell.x, cell.y
            cell.s += sp * det(x, y, odx, ody, dx, dy) / \
                    sqrt((x-dx)**2 + (y-dy)**2) / 5.
            cell.s *= sl
            cell.c += cell.s
        self.odx, self.ody = self.dx, self.dy

    def draw(self):
        for cell in self.cells:
            x, y, s, c = cell.x, cell.y, cell.s, cell.c
            d = self.bd * s + .001
            set_color(.5, .5, max(0, min(1, .5 + d)), .8)
            drawLine([x, y, x + d * cos(c) + 0.1, y + d * sin(c) + 0.1])


#
# Inspiration from dotlassie
# http://www.openprocessing.org/visuals/?visualID=3692
#

class VizScenarioSmoke(MTWidget):
    title = 'Smoke'
    author = 'dotlassie'
    def __init__(self):
        super(VizScenarioSmoke, self).__init__()
        self.t = 0
        self.w = 64
        self.m = 0
        self.x = 0
        self.z = 16
        self.pixels = array('B', '\x00' * self.w * self.w * 3)
        self.texture = Texture.create(self.w, self.w, format=GL_RGB)

    @staticmethod
    def noise(x, y, z):
        # Perlin noise !
        p = (
        151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,
        30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,
        62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
        125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,
        83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,
        143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,
        196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,
        250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,
        58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,
        221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,
        224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,
        12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,
        199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,
        205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180,
        151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,140,36,103,
        30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,75,0,26,197,
        62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,56,87,174,20,
        125,136,171,168,68,175,74,165,71,134,139,48,27,166,77,146,158,231,
        83,111,229,122,60,211,133,230,220,105,92,41,55,46,245,40,244,102,
        143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,89,18,169,200,
        196,135,130,116,188,159,86,164,100,109,198,173,186,3,64,52,217,226,
        250,124,123,5,202,38,147,118,126,255,82,85,212,207,206,59,227,47,16,
        58,17,182,189,28,42,223,183,170,213,119,248,152,2,44,154,163,70,
        221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,110,79,113,
        224,232,178,185,112,104,218,246,97,228,251,34,242,193,238,210,144,
        12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,214,31,181,
        199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,138,236,
        205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180)

        def lerp(t, a, b):
            return a + t * (b - a)

        def fade(t):
            return t * t * t * (t * (t * 6 - 15) + 10)

        def grad(hash, x, y, z):
            h = hash & 15
            if h < 8:
                u = x
            else:
                u = y
            if h < 4:
                v = y
            elif h == 12 or h == 14:
                v = x
            else:
                v = z
            if h & 1 != 0:
                u = -u
            if h & 2 != 0:
                v = -v
            return u + v

        X = int(floor(x)) & 255
        Y = int(floor(y)) & 255
        Z = int(floor(z)) & 255
        x -= floor(x)
        y -= floor(y)
        z -= floor(z)

        u = fade(x)
        v = fade(y)
        w = fade(z)

        A =  p[X] + Y
        AA = p[A] + Z
        AB = p[A + 1] + Z
        B =  p[X + 1] + Y
        BA = p[B] + Z
        BB = p[B + 1] + Z

        pAA = p[AA]
        pAB = p[AB]
        pBA = p[BA]
        pBB = p[BB]
        pAA1 = p[AA + 1]
        pBA1 = p[BA + 1]
        pAB1 = p[AB + 1]
        pBB1 = p[BB + 1]

        gradAA =  grad(pAA, x,   y,   z)
        gradBA =  grad(pBA, x-1, y,   z)
        gradAB =  grad(pAB, x,   y-1, z)
        gradBB =  grad(pBB, x-1, y-1, z)
        gradAA1 = grad(pAA1,x,   y,   z-1)
        gradBA1 = grad(pBA1,x-1, y,   z-1)
        gradAB1 = grad(pAB1,x,   y-1, z-1)
        gradBB1 = grad(pBB1,x-1, y-1, z-1)
        return lerp(w,
        lerp(v, lerp(u, gradAA, gradBA), lerp(u, gradAB, gradBB)),
        lerp(v, lerp(u, gradAA1,gradBA1),lerp(u, gradAB1,gradBB1)))


    def on_update(self):
        w = self.w
        p = self.pixels
        z = self.z
        z2 = self.z / 2.
        wf = float(self.w)
        t = self.t
        noise = self.noise
        self.t += getFrameDt() / 2.

        if vizfast:
            return vizfast.smokeUpdate(w, p, z, z2, wf, t)

        for x in xrange(w * w):
            X = ((x % w) / wf) * z - z2
            Y = ((x / w) / wf) * z - z2
            cl = max(0, min(255, int((noise(X, Y, self.t) - .3) * 512)))
            p[x*3] = cl
            p[x*3+1] = cl
            p[x*3+2] = min(255, cl * 2)

    def on_touch_move(self, touch):
        self.t += touch.sx - 0.5
        self.z = 5 + touch.sy * 20


    def draw(self):
        m2 = self.w * 2
        w, h = size = (m2, m2)
        x, y = pos = (w2 - m2 / 2, h2 - m2 / 2)

        self.texture.blit_buffer(self.pixels.tostring())

        set_color(.5, .5, .8, .5)
        drawRectangle(pos=(x-2, y-2), size=(w+4, h+4))
        set_color(1)
        drawTexturedRectangle(texture=self.texture, size=size, pos=pos)


#
# Inspiration from jose henrique padovani
# http://www.openprocessing.org/visuals/?visualID=3693
#

class VizScenarioEmotive(MTWidget):
    title = 'Emotive'
    author = 'Jose Henrique Padovani'
    def __init__(self, **kwargs):
        super(VizScenarioEmotive, self).__init__()
        self.emotions = []
        for x in (':)', ';)', ':P', ':O', ':o', ':|', '8)'):
            self.emotions.append(getLabel(x, font_size=180).texture)
        self.delay = 0
        self.idx = 0

    def draw(self):
        self.delay += getFrameDt()
        if self.delay > 2 + random() * 5:
            self.idx = int(random() * len(self.emotions))
            self.delay = 0
        emotion = self.emotions[self.idx]
        set_color(1, blend=True)
        with gx_matrix:
            glTranslatef(w2, h2, 0)
            glRotatef(-90, 0, 0, 1)
            drawTexturedRectangle(texture=emotion,
                                  pos=(-emotion.width / 2., -emotion.height / 2.),
                                  size=emotion.size)

    def on_touch_down(self, touch):
        self.delay += 100

#
# Inspiration from William Birtchnell
# http://www.openprocessing.org/visuals/?visualID=7035
#

class VizScenarioPlasma(MTWidget):
    title = 'Plasma'
    author = 'William Birtchnell'
    def __init__(self):
        super(VizScenarioPlasma, self).__init__()
        self.w = 256
        self.wave = array('i', [0] * 2000)
        self.wave2 = array('i', [0] * 2000)
        self.luma = array('i', [0] * 1024)
        self.mpos = array('i', [0] * 3 * 2 * 2) #zyx
        self.cWaves = array('i', [0] * 1300 * 2 * 2) #zyx
        self.pixels = array('B', '\x00' * self.w * self.w * 3)
        self.texture = Texture.create(self.w, self.w, format=GL_RGB)

        for i in xrange(3 * 2 * 2):
            self.mpos[i] = int(random() * 512)
        for i in xrange(2000):
            self.wave[i] = int(100 + (sin(i*6.28318531/720)*100))
            self.wave2[i] = int(64 + (sin(i*6.28318531/360)*64))
        for ix in xrange(1024):
            iy = ix
            while iy > 255 or iy < 0:
                if iy > 255: iy = 511 - iy
                if iy < 0: iy = abs(iy)
            if iy > 201:
                iy = (iy * 4) - (201 * 3)
            iy = int((iy * 255) / ((255 * 4.) - (201 * 3)))
            self.luma[ix] = iy

    def on_update(self):
        pos = self.mpos
        cWaves = self.cWaves
        wave = self.wave
        wave2 = self.wave2
        pixels = self.pixels
        luma = self.luma
        w = self.w

        if vizfast:
            return vizfast.plasmaUpdate(pos, cWaves, wave, wave2, pixels, luma, w)

        for ix in xrange(2):
            for iy in xrange(2):
                for iz in xrange(3):
                    i = ix * 2 * 2 + iy * 2 + iz
                    if ix + iy == 1:
                        pos[i] += 2 + int(random() * 2)
                        if pos[i] > 719:
                            pos[i] -= 720
                    else:
                        pos[i] -= 2 + int(random() * 2)
                        if pos[i] < 0:
                            pos[i] += 720
        for ix in xrange(w):
            for iy in xrange(3):
                for iz in xrange(2):
                    i = iz * 3 * w + iy * w + ix
                    ip = (iz * 2 + iy)
                    ip2 = (1 * 2 * 2 + iz * 2 + iy)
                    cWaves[i] = wave[ix + pos[ip]] + wave2[ix + pos[ip2]]

        for ix in xrange(w):
            for iy in xrange(w):
                # I0 + I1 * w + I2 * w * 3
                pixels[iy * w * 3 + ix * 3] = \
                        luma[cWaves[ix] + cWaves[iy + w * 3]]
                pixels[iy * w * 3 + ix * 3 + 1] = \
                        luma[cWaves[ix + w] + cWaves[iy + w + w * 3]]
                pixels[iy * w * 3 + ix * 3 + 2] = \
                        luma[cWaves[ix + w * 2] + cWaves[iy + w * 2 + w * 3]]

    def draw(self):
        w = self.w
        m2 = w * 2
        w, h = size = (m2, m2)
        x, y = pos = (w2 - m2 / 2, h2 - m2 / 2)
        self.texture.blit_buffer(self.pixels.tostring())
        set_color(.5, .5, .8, .5)
        drawRectangle(pos=(x-2, y-2), size=(w+4, h+4))
        set_color(1)
        drawTexturedRectangle(texture=self.texture, size=size, pos=pos)


#
# Main class for control
#

class VizPlay(MTWidget):
    def __init__(self, **kwargs):
        super(VizPlay, self).__init__(**kwargs)
        self.scenarios = []
        self.current = None
        self.nextidx = 0
        self.state = 0
        self.out_alpha = 0
        self.info_alpha = 1

    def add_scenario(self, scn):
        if self.current is None:
            self.current = scn
            self.add_widget(self.current)
        self.scenarios.append(scn)

    def on_touch_down(self, touch):
        if touch.y < 70:
            if touch.x < 100:
                self.goto(-1)
                return True
            if touch.x > ww - 100:
                self.goto(1)
                return True
        return super(VizPlay, self).on_touch_down(touch)

    def goto(self, s):
        self.nextidx = (self.nextidx + s) % len(self.scenarios)
        self.state = 1

    def on_draw(self):
        d = getFrameDt() * 2.
        # state machine
        if self.state == 1:
            # fade out the current screen
            self.delay = 0
            self.out_alpha += d
            if self.out_alpha >= 1.:
                self.out_alpha = 1
                self.state = 2
        elif self.state == 2:
            # change screen
            self.remove_widget(self.current)
            self.current = self.scenarios[self.nextidx]
            self.add_widget(self.current)
            self.state = 3
        elif self.state == 3:
            self.info_alpha = 1
            self.out_alpha -= d
            if self.out_alpha <= 0:
                self.out_alpha = 0
                self.state = 4
        elif self.state == 4:
            self.delay += d / 2.
            if self.delay >= 3:
                self.delay = 0
                self.state = 5
        elif self.state == 5:
            self.info_alpha -= d / 6.
            if self.info_alpha <= 0:
                self.state = 0

        # background
        set_color(0)
        drawRectangle(size=ws)

        # us
        super(VizPlay, self).on_draw()

        # info alpha
        ia = self.info_alpha

        # bottom bar
        set_color(59/255., 126/255., 197/255., .3 * ia)
        drawRectangle(size=(ww, 50))

        # title
        drawLabel(label=self.current.title,
                  font_size=22,
                  color=(1, 1, 1, .7 * ia),
                  pos=(w2, 30))
        drawLabel(label=self.current.author,
                  font_size=10,
                  color=(1, 1, 1, .5 * ia),
                  pos=(w2, 12))

        # next / previous
        drawLabel(label='<',
                  font_size=42,
                  color=(.8, .8, 1, .4),
                  pos=(30, 25))

        # previous
        drawLabel(label='>',
                  font_size=42,
                  color=(.8, .8, 1, .4),
                  pos=(ww - 30, 25))

        # draw FPS
        drawLabel(label='%.2f' % getClock().get_fps(),
                  font_size=20,
                  color=(.8, .8, .8, .4),
                  pos=(10, wh - 36),
                  center=False)


        # out
        if self.out_alpha > 0:
            set_color(0, 0, 0, self.out_alpha)
            drawRectangle(size=ws)

if __name__ == '__main__':
    viz = VizPlay()
    viz.add_scenario(VizScenarioWater())
    viz.add_scenario(VizScenarioBlob())
    viz.add_scenario(VizScenarioTree())
    viz.add_scenario(VizScenarioEmpathy())
    viz.add_scenario(VizScenarioSmoke())
    viz.add_scenario(VizScenarioEmotive())
    viz.add_scenario(VizScenarioPlasma())
    runTouchApp(viz)
