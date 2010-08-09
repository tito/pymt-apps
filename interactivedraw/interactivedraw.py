from pymt import *
from easygui import EasyGui
from math import pi, cos, sin, atan2, sqrt, radians, copysign
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from array import array
from time import time

css_add_sheet('''
basewindow {
    bg-color: rgb(0, 0, 0);
}''')
css_reload();


class GLPerspectiveWidget(MTWidget):
    def __init__(self, **kwargs):
        super(GLPerspectiveWidget, self).__init__(**kwargs)
        self.a = 0

    def on_draw(self):
        self.draw3D()
        self.drawUI()
        for x in self.children:
            x.dispatch_event('on_draw')

    def draw3D(self):
        glEnable(GL_DEPTH_TEST)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, self.width / float(self.height), 1., 10000.)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        self.a += getFrameDt()
        w2, h2 = self.width / 2., self.height / 2.
        if self.mode == 'replay':
            '''
            gluLookAt(w2 + cos(self.a) * self.width, h2,
                      sin(self.a) * 1000, w2, h2, cos(self.a) * 1000, 0, 1, 0)
            gluLookAt(-400, 400, 400, w2, h2, 0, 0, 1, 0)
            '''
            gluLookAt(self.camx, self.camy, 1000, w2, h2, 0, 0, 1, 0)
        else:
            gluLookAt(w2, h2, 1000, w2, h2, 0, 0, 1, 0)

        self.draw()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glDisable(GL_DEPTH_TEST)

def smooth_stroke(resolution, sketch):
    out = []
    for j in xrange(4, len(sketch)):
        startPos = j - 3
        
        x0 = sketch[startPos][0]
        y0 = sketch[startPos][1]
        z0 = sketch[startPos][2]
        d0 = sketch[startPos][3]
        x1 = sketch[startPos + 1][0]
        y1 = sketch[startPos + 1][1]
        z1 = sketch[startPos + 1][2]
        d1 = sketch[startPos + 1][3]
        x2 = sketch[startPos + 2][0]
        y2 = sketch[startPos + 2][1]
        z2 = sketch[startPos + 2][2]
        d2 = sketch[startPos + 2][3]
        x3 = sketch[startPos + 3][0]
        y3 = sketch[startPos + 3][1]
        z3 = sketch[startPos + 3][2]
        d3 = sketch[startPos + 3][3]
        
        for i in xrange(1, resolution):
            t  =  float(i) / float(resolution - 1)
            t2 = t * t
            t3 = t2 * t
            
            x = 0.5 * ( ( 2.0 * x1 ) +
                        ( -x0 + x2 ) * t +
                        ( 2.0 * x0 - 5.0 * x1 + 4 * x2 - x3 ) * t2 +
                        ( -x0 + 3.0 * x1 - 3.0 * x2 + x3 ) * t3 )
            
            y = 0.5 * ( ( 2.0 * y1 ) +
                        ( -y0 + y2 ) * t +
                        ( 2.0 * y0 - 5.0 * y1 + 4 * y2 - y3 ) * t2 +
                        ( -y0 + 3.0 * y1 - 3.0 * y2 + y3 ) * t3 )

            z = 0.5 * ( ( 2.0 * z1 ) +
                        ( -z0 + z2 ) * t +
                        ( 2.0 * z0 - 5.0 * z1 + 4 * z2 - z3 ) * t2 +
                        ( -z0 + 3.0 * z1 - 3.0 * z2 + z3 ) * t3 )

            d = 0.5 * ( ( 2.0 * d1 ) +
                        ( -d0 + d2 ) * t +
                        ( 2.0 * d0 - 5.0 * d1 + 4 * d2 - d3 ) * t2 +
                        ( -d0 + 3.0 * d1 - 3.0 * d2 + d3 ) * t3 )
               
               
            out.append((x, y, z, d))
    return out


class Canvas(GLPerspectiveWidget):
    def __init__(self, **kwargs):
        super(Canvas, self).__init__(**kwargs)
        self.sketch = []
        self.sketchtime = 0
        self.sketchidx = 0
        self.replaytime = 0
        self.replaytimeaction = 0
        self.sketchduration = 0
        self.result = []
        self._dirty = False
        self.dirtytime = 0
        self.mode = 'record'
        self.vbo = vbo.VBO('', usage=GL_DYNAMIC_DRAW, target=GL_ARRAY_BUFFER)
        w2, h2 = self.width / 2., self.height / 2.
        self.camx, self.camy = w2, h2
        self.gui = self.buildui()

    def buildui(self):
        gui = EasyGui(size=(200, self.height), mode='twoline')
        gui.panel('OpenGL')
        gui.slider('Fog start', 'fog_start', 800, 0, 5000)
        gui.slider('Fog end', 'fog_end', 2500, 0, 5000)
        gui.slider('Speed', 'speed', 100, 1, 200)
        gui.slider('Opacity', 'opacity', 1., 0., 1.)
        gui.toggle('Draw outline', 'draw_outline', True)
        gui.slider('Outline width', 'outline_width', 1.5, 0., 5.)
        gui.slider('Resolution', 'resolution', 5, 2, 20)
        gui.slider('Z', 'z', 50, 20, 400)
        gui.connect('on_change', self.on_gui_change)
        self.add_widget(gui)
        return gui

    def on_gui_change(self, key, value):
        if key in ('resolution', 'z'):
            self.dirty = True

    def _set_dirty(self, x):
        self.dirtytime = time()
        self._dirty = x
    def _get_dirty(self):
        return self._dirty
    dirty = property(_get_dirty, _set_dirty)

    def on_touch_down(self, touch):
        ret = super(Canvas, self).on_touch_down(touch)
        if ret:
            return True
        touch.grab(self)
        if touch.is_double_tap:
            self.result = []
            self.sketch = []
            self.sketchidx = 0
            self.mode = 'record'
        if self.mode == 'replay':
            return
        if len(self.sketch) == 0:
            self.sketchtime = time()

        if len(self.sketch) == 0:
            dist = 20
        else:
            va = self.sketch[-1]
            vb = touch.pos
            dist = sqrt((va[0] - vb[0]) ** 2 + (va[1] - vb[1]) ** 2)
        self.sketch.append([touch.x, touch.y, time() - self.sketchtime, dist])
        self.dirty = True

    def on_touch_move(self, touch):
        ret = super(Canvas, self).on_touch_move(touch)
        if ret:
            return True
        if touch.grab_current != self:
            return
        if self.mode == 'replay':
            self.camy += (touch.y - touch.dypos) * 5.
            self.camx += (touch.x - touch.dxpos) * 5.
            return
        va = self.sketch[-1]
        vb = touch.pos
        dist = sqrt((va[0] - vb[0]) ** 2 + (va[1] - vb[1]) ** 2)
        self.sketch.append([touch.x, touch.y, time() - self.sketchtime, dist])
        self.dirty = True

    def on_update(self):
        super(Canvas, self).on_update()
        if self.mode == 'record' and \
           len(self.sketch) > 0 and \
           len(getCurrentTouches()) == 0 and \
           time() - self.dirtytime > 1.:
            self.mode = 'replay'
            self.replaytime = time()
            self.sketchduration = time() - self.sketchtime
        if not self.dirty:
            return
        self.compute_sketch()
        self.dirty = False

    def compute_sketch(self):
        if len(self.sketch) < 2:
            self.result = []
            return

        self.render_sketch = smooth_stroke(self.gui.values.get('resolution'), self.sketch)
        self.result = []

        dist = 100
        r = self.result
        rt = []
        v = self.render_sketch

        # compute all the next points
        va = None
        a90 = radians(90)
        for vb in v:
            if va is None:
                va = vb
                continue
            a = atan2(vb[1] - va[1], vb[0] - va[0])
            dist = 60 - boundary(va[3], 10, 50)
            r.extend([
                va[0] + cos(a - a90) * dist,
                va[1] + sin(a - a90) * dist,
                va[2] * self.gui.values.get('z'),
                va[0] + cos(a + a90) * dist,
                va[1] + sin(a + a90) * dist,
                va[2] * self.gui.values.get('z'),
            ])
            rt.append(vb[2])
            va = vb

        self.result = r
        self.result_timeline = rt
        self.vbo.set_array(array('f', self.result).tostring())
        self.index0 = range(0, len(self.result) / 3, 2)
        self.index1 = range(1, len(self.result) / 3, 2)

    def draw(self):
        if len(self.result) == 0:
            return

        r = self.result

        # found index to draw
        if self.mode == 'replay':
            self.replaytimeaction += getFrameDt() * self.gui.values.get('speed') / 100.
            if self.replaytimeaction > self.sketchduration:
                self.replaytimeaction = 0
            i = len([x for x in self.result_timeline if x <= self.replaytimeaction])
            r3 = i * 2
        else:
            r3 = len(self.result) / 3

        r6 = r3 / 2

        glFogfv(GL_FOG_COLOR, (0, 0, 0))
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_DENSITY, .02)
        glFogf(GL_FOG_START, self.gui.values.get('fog_start'))
        glFogf(GL_FOG_END, self.gui.values.get('fog_end'))
        glEnable(GL_FOG)

        glLineWidth(self.gui.values.get('outline_width'))
        with self.vbo:
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, None)

            set_color(1, 1, 1, self.gui.values.get('opacity'), blend=True)
            glDrawArrays(GL_QUAD_STRIP, 0, r3)

            if self.gui.values.get('draw_outline'):
                glTranslatef(0, 0, .75)
                set_color(0, 0, 0, .7, blend=True)
                glDrawElements(GL_LINE_STRIP, r6, GL_UNSIGNED_INT, self.index0)
                glDrawElements(GL_LINE_STRIP, r6, GL_UNSIGNED_INT, self.index1)

        glDisable(GL_FOG)

    def drawUI(self):
        drawLabel(label='mode:%s size:%d' % (
            self.mode, len(self.sketch)),
            center=False)



if __name__ == '__main__':
    runTouchApp(Canvas(size=getWindow().size))
