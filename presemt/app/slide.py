__all__ = ('Slide', )

import os
from pymt import MTWidget, MTScatterWidget, set_color, drawRectangle

class EditProxy(MTWidget):
    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        super(EditProxy, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if not self.ctx.mode == 'layout':
            return super(EditProxy, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.ctx.mode == 'layout':
            return super(EditProxy, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.ctx.mode == 'layout':
            return super(EditProxy, self).on_touch_up(touch)


class SlideItem(MTScatterWidget):
    name = 'generic'
    def __init__(self, ctx, **kwargs):
        kwargs.setdefault('restoremode', False)
        self.do_draw = False
        self.ctx = ctx
        self.locked = True
        self.proxy = EditProxy(self.ctx)
        self.restoremode = kwargs.get('restoremode')
        super(SlideItem, self).__init__(**kwargs)
        super(SlideItem, self).add_widget(self.proxy)

    @property
    def circle(self):
        x, y = self.center
        return x, y, max(self.width, self.height)

    def _get_state(self):
        return { 'matrix': super(SlideItem, self)._get_state(),
                 'locked': self.locked,
                 'name': self.name }
    def _set_state(self, state):
        self.locked = state.get('locked')
        super(SlideItem, self)._set_state(state.get('matrix'))

    def clean_filename(self, filename):
        # strip the curdir if possible
        curdir = os.path.realpath(os.path.curdir) + os.path.sep
        if filename.startswith(curdir):
            filename = filename[len(curdir):]
        # make it crossplatform
        return filename.replace(os.path.sep, '/')

    def add_widget(self, widget, front=True):
        self.proxy.add_widget(widget, front)

    def draw(self):
        if self.ctx.mode == 'layout':
            set_color(0,1,0)
            drawRectangle(pos=(-10,-10),size=(self.width+20,self.height+20))
        elif self.ctx.mode == 'edit':
            set_color(1,1,0)
            drawRectangle(pos=(-10,-10),size=(self.width+20,self.height+20))

    @staticmethod
    def draw_drag_icon(self=None):
        set_color(1,0,1)
        drawRectangle(pos=(-30,-30),size=(60,60))

    def on_touch_down(self, touch):
        if self.ctx.mode == 'layout' and touch.is_double_tap \
           and self.collide_point(*touch.pos):
            self.parent.remove_widget(self)
            return True
        if not (self.ctx.mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if not (self.ctx.mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if not (self.ctx.mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_up(touch)

    def on_move(self, *largs):
        self.ctx.set_dirty()
