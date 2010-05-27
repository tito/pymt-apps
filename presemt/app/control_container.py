__all__ = ('SlideContainer', )

from os import path
from pymt import MTScatterPlane, set_color, drawLine, set_brush, gx_matrix
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

    def on_draw(self):
        super(SlideContainer, self).on_draw()
        with gx_matrix:
            glMultMatrixf(self.transform_mat)
            glLineWidth(3)
            set_color(0, 0, 0, .8)
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