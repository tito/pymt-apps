__all__ = ('SlideImage', )

from pymt import Image, MTFileBrowser
from slide import SlideItem

class SlideImage(SlideItem):
    name = 'image'
    def __init__(self, *largs, **kwargs):
        super(SlideImage, self).__init__(*largs, **kwargs)
        self._filename = ''
        self.image = None
        self.filename = 'content/1.png'
        self.fb = None

    def _get_filename(self):
        return self._filename
    def _set_filename(self, filename):
        self._filename = self.clean_filename(filename)
        try:
            self.image = Image(self._filename)
            self.ctx.set_dirty()
        except:
            pass
        self.width = (self.image.width / float(self.image.height)) * self.height
    filename = property(_get_filename, _set_filename)

    def draw(self):
        super(SlideImage, self).draw()
        self.image.size = self.size
        self.image.draw()

    def on_touch_down(self, touch):
        if self.ctx.mode == 'edit' and self.collide_point(*touch.pos):
            if self.fb is None:
                self.fb = MTFileBrowser(pos =(100,100), filters=(
                    '.*\.[Pp][Nn][Gg]$',
                    '.*\.[Jj][Pp][Gg]$',
                    '.*\.[Jj][Pp][Ee][Gg]$',
                ))
                self.fb.push_handlers(on_select=self.load_file)
            self.get_root_window().remove_widget(self.fb)
            self.get_root_window().add_widget(self.fb)
            return True
        else:
            return super(SlideImage, self).on_touch_down(touch)

    def load_file(self, files):
        self.filename = files[0]

    def _get_state(self):
        d = super(SlideImage, self)._get_state()
        d['image'] = self.filename
        return d

    def _set_state(self, state):
        super(SlideImage, self)._set_state(state)
        self.filename = state.get('image')


