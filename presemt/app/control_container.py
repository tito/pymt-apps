__all__ = ('SlideContainer', )

from pymt import MTScatterPlane, set_color
from array import array
from OpenGL.GL import *
from OpenGL.arrays import vbo

class SlideContainer(MTScatterPlane):
    def __init__(self, ctx, **kwargs):
        super(SlideContainer, self).__init__(**kwargs)
        self.ctx = ctx
        self.vbo = vbo.VBO('', usage=GL_STREAM_DRAW, target=GL_ARRAY_BUFFER)
        self.show_grid = True
        
        lines = array('f')
        for i in range(-1000,1000):
            lines.extend((i*50, -50000, i*50, 50000))
            lines.extend((-50000, i*50, 50000, i*50))
        self.vbo.set_array(lines.tostring())

    def draw(self):
        if not self.show_grid:
            return
        set_color(*self.style.get('grid-color'))
        glLineWidth(1)
        glEnableClientState(GL_VERTEX_ARRAY)
        with self.vbo:
            glVertexPointer(2, GL_FLOAT, 0, None)
            glDrawArrays(GL_LINES, 0, len(self.vbo))
        glDisableClientState(GL_VERTEX_ARRAY)

    def add_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).add_widget(*largs)

    def remove_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).remove_widget(*largs)
