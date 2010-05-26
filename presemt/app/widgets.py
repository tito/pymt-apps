__all__ = ('PresemtButton', 'PresemtToggleButton')

from pymt import MTImageButton

class PresemtButton(MTImageButton):
    def draw(self):
        super(MTImageButton, self).draw()
        super(PresemtButton, self).draw()

class PresemtToggleButton(PresemtButton):
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if self.state == 'down':
            self.state = 'normal'
        else:
            self.state = 'down'
        self.dispatch_event('on_press', touch)
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if not touch.grab_current == self:
            return False
        touch.ungrab(self)
        self.state = self.state
        if self.collide_point(*touch.pos):
            self.dispatch_event('on_release', touch)
        return True

