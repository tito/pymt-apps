from pymt import MTVideo, MTFileBrowser
from slide import SlideItem

class SlideVideo(SlideItem):
    name = 'video'
    def __init__(self, *largs, **kwargs):
        super(SlideVideo, self).__init__(*largs, **kwargs)
        self._filename = ''
        self.video = None
        self.locked = False
        self.filename = 'content/softboy.avi'

    def _get_filename(self):
        return self._filename
    def _set_filename(self, filename):
        self._filename = filename
        try:
            if self.video:
                self.remove_widget(self.video)
            self.video = MTVideo(filename=self._filename,
                                 on_playback_end='loop',
                                 volume=0.1)
            self.add_widget(self.video)
            self.ctx.set_dirty()
        except:
            pass
        self.width = (self.video.width / float(self.video.height)) * self.height
    filename = property(_get_filename, _set_filename)

    def draw(self):
        self.size = self.video.size
        super(SlideVideo, self).draw()

    def on_touch_down(self, touch):
        if self.ctx.mode == 'edit' and self.collide_point(*touch.pos):
            fb = MTFileBrowser(pos=(100,100), filters=(
                '.*\.[Aa][Vv][Ii]$',
                '.*\.[Mm][Pp][Gg]$',
                '.*\.[Mm][Pp][Ee][Gg]$',
                '.*\.[Mm][Kk][Vv]$'
            ))
            fb.push_handlers(on_select=self.load_file)
            self.get_root_window().add_widget(fb)
            return True
        return super(SlideVideo, self).on_touch_down(touch)

    def load_file(self, files):
        self.filename = files[0]

    def _get_state(self):
        d = super(SlideVideo, self)._get_state()
        d['video'] = self.filename
        return d

    def _set_state(self, state):
        super(SlideVideo, self)._set_state(state)
        self.filename = state.get('video')


