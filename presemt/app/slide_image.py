__all__ = ('SlideImage', )

from pymt import Image, MTFileBrowser, Loader
from slide import SlideItem

class SlideImage(SlideItem):
    name = 'image'
    def __init__(self, *largs, **kwargs):
        super(SlideImage, self).__init__(*largs, **kwargs)
        self._filename = ''
        self.is_loaded = False
        self.image = None
        if self.restoremode is False:
            self.filename = 'content/1.png'
        self.fb = None

    def _get_filename(self):
        return self._filename
    def _set_filename(self, filename):
        self._filename = self.clean_filename(filename)
        try:
            self.is_loaded = False
            self.image = Loader.image(self._filename)
            if self.image.loaded is False:
                self.image.connect('on_load', self._image_on_load)
            else:
                self._image_on_load()
            self.ctx.set_dirty()
        except:
            raise
    filename = property(_get_filename, _set_filename)

    def _image_on_load(self, *largs):
        self.is_loaded = True
        self.width = (self.image.width / float(self.image.height)) * self.height

    def draw(self):
        super(SlideImage, self).draw()
        if self.image:
            self.image.size = self.size
            self.image.draw()

    def on_touch_down(self, touch):
        if self.ctx.mode == 'edit' and self.collide_point(*touch.pos):
            self.ctx.open_filebrowser(self.load_file, (
                '.*\.[Pp][Nn][Gg]$',
                '.*\.[Jj][Pp][Gg]$',
                '.*\.[Jj][Pp][Ee][Gg]$',
            ))
            return True
        else:
            return super(SlideImage, self).on_touch_down(touch)

    def load_file(self, filename):
        self.filename = filename

    def _get_state(self):
        d = super(SlideImage, self)._get_state()
        d['image'] = self.filename
        return d
    def _set_state(self, state):
        super(SlideImage, self)._set_state(state)
        self.filename = state.get('image')
    state = property(_get_state, _set_state)


