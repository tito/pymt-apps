__all__ = ('SlideContainer', )

from os import path
from pymt import MTScatterPlane, set_color, drawLine, set_brush, gx_matrix, \
                getWindow, drawPolygon, MTWidget
from array import array
from tesselator import Tesselator
from OpenGL.GL import *
from OpenGL.arrays import vbo

class SlideGroup(MTWidget):
    groupid = 1
    def __init__(self, **kwargs):
        super(SlideGroup, self).__init__(**kwargs)
        self.do_draw = True
        self.update_size()
        self.groupid = SlideGroup.groupid
        SlideGroup.groupid += 1

    def update_size(self, *largs):
        minx, miny, maxx, maxy = 999, 999, -999, -999
        for child in self.children:
            x, y, r = child.circle
            minx = min(minx, x-r)
            miny = min(minx, y-r)
            maxx = max(maxx, x+r)
            maxy = max(maxy, y+r)
        self.pos = minx, miny
        self.size = maxx-minx, maxy-miny
        x, y = self.center
        self.circle = x, y, max(self.width, self.height)

    def add_widget(self, widget):
        widget.connect('on_transform', self.update_size)
        super(SlideGroup, self).add_widget(widget)
        self.update_size()

    def on_update(self):
        w, h = getWindow().size
        for child in self.children[:]:
            child.dispatch_event('on_update')
            # update child only if we are drawing too
            if self.do_draw:
                x, y, r = child.circle
                x, y = self.parent.to_parent(x, y)
                r *= self.parent.scale
                if x+r < 0 or x-r > w or y+r < 0 or y-r > h:
                    child.do_draw = False
                else:
                    child.do_draw = True


    def on_draw(self):
        for child in [x for x in self.children if x.do_draw]:
            child.dispatch_event('on_draw')

class SlideContainer(MTScatterPlane):
    def __init__(self, ctx, **kwargs):
        super(SlideContainer, self).__init__(**kwargs)
        self.ctx = ctx
        self.vbo = vbo.VBO('', usage=GL_STREAM_DRAW, target=GL_ARRAY_BUFFER)
        self.linepen = []
        self.dirty = True
        self.show_grid = True
        self.selection = []
        self.groupid = 0

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

    def on_draw(self):
        w, h = getWindow().size
        with gx_matrix:
            glMultMatrixf(self.transform_mat)
            self.draw()
            for child in [x for x in self.children if x.do_draw]:
                child.dispatch_event('on_draw')
            # draw pen
            glLineWidth(3)
            set_color(.8, .8, .8, .8)
            for x in self.linepen:
                drawLine(x)
            # draw selection
            if len(self.selection) > 2:
                set_color(.2, .6, .2, .8)
                drawLine(self.selection)
                set_color(.2, .6, .2, .3)
                drawLine(self.selection[-1] + self.selection[0])

    def on_touch_down(self, touch):
        if self.ctx.mode == 'live' and touch.device == 'wm_pen':
            if touch.is_double_tap:
                self.linepen = []
                return True
            self.linepen.append(list(self.to_local(*touch.pos)))
            return True
        if self.ctx.mode == 'layout' and touch.device == 'wm_pen':
            self.selection = [touch.pos]
            return True
        return super(SlideContainer, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.ctx.mode == 'live' and touch.device == 'wm_pen':
            if len(self.linepen):
                self.linepen[-1].extend(self.to_local(*touch.pos))
            return True
        if self.ctx.mode == 'layout' and touch.device == 'wm_pen':
            self.selection.append(touch.pos)
            return True
        return super(SlideContainer, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.ctx.mode == 'layout' and touch.device == 'wm_pen':
            self.apply_group_from_selection()
            return True
        return super(SlideContainer, self).on_touch_up(touch)

    def add_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).add_widget(*largs)

    def remove_widget(self, *largs):
        self.ctx.set_dirty()
        super(SlideContainer, self).remove_widget(*largs)

    def apply_group_from_selection(self):
        in_selection = self.in_selection
        group = []
        for child in self.children:
            if child.__class__ == SlideGroup:
                for subchild in child.children:
                    if in_selection(*subchild.center):
                        group.append(subchild)
            elif in_selection(*child.center):
                group.append(child)
        self.selection = []

        w = SlideGroup()
        for x in group:
            x.parent.remove_widget(x)
            w.add_widget(x)
        self.add_widget(w)

    def in_selection(self, x, y):
        n = len(self.selection)
        if n < 2:
            return False
        inside = False
        nodes = self.selection
        p1x, p1y = nodes[0]
        for i in xrange(n + 1):
            p2x,p2y = nodes[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y
        return inside
