__all__ = ('SlideContainer', )

from os import path
from pymt import MTScatterPlane, set_color, drawLine, set_brush, gx_matrix, getWindow
from array import array
from OpenGL.GL import *
from OpenGL.arrays import vbo

class SlideContainer(MTScatterPlane):
    def __init__(self, ctx, **kwargs):
        super(SlideContainer, self).__init__(**kwargs)
        self.ctx = ctx
        self.vbo = vbo.VBO('', usage=GL_STREAM_DRAW, target=GL_ARRAY_BUFFER)
        self.linepen = []
        self.dirty = True
        self.show_grid = True

        self.lcount = 0
        lines = array('f')
        for i in range(-1000,1000):
            lines.extend((i*50, -50000, i*50, 50000))
            lines.extend((-50000, i*50, 50000, i*50))
            self.lcount += 4
        self.vbo.set_array(lines.tostring())

    def draw(self):
        if not self.show_grid:
            return
        set_color(*self.style.get('grid-color'))
        glLineWidth(1)
        glEnableClientState(GL_VERTEX_ARRAY)
        with self.vbo:
            glVertexPointer(2, GL_FLOAT, 0, None)
            glDrawArrays(GL_LINES, 0, self.lcount)
        glDisableClientState(GL_VERTEX_ARRAY)

    def on_update(self):
        scale = self.scale
        w, h = getWindow().size
        for child in self.children[:]:
            x, y, r = child.circle
            x, y = self.to_parent(x, y)
            r *= self.scale
            if x+r < 0 or x-r > w or y+r < 0 or y-r > h:
                child.do_draw = False
                continue
            else:
                child.do_draw = True
            child.dispatch_event('on_update')
        self.draw()

    def on_draw(self):
        w, h = getWindow().size
        with gx_matrix:
            glMultMatrixf(self.transform_mat)
            self.draw()
            for child in [x for x in self.children if x.do_draw]:
                child.dispatch_event('on_draw')
            glLineWidth(3)
            set_color(.8, .8, .8, .8)
            for x in self.linepen:
                drawLine(x)

    def on_touch_down(self, touch):
        if self.ctx.mode == 'live' and touch.device == 'wm_pen':
            if touch.is_double_tap:
                self.linepen = []
                return True
            self.linepen.append(list(self.to_local(*touch.pos)))
            return True
        return super(SlideContainer, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.ctx.mode == 'live' and touch.device == 'wm_pen':
            if len(self.linepen):
                self.linepen[-1].extend(self.to_local(*touch.pos))
            return True
        return super(SlideContainer, self).on_touch_move(touch)

    def add_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).add_widget(*largs)

    def remove_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).remove_widget(*largs)
