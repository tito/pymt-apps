__all__ = ('WorkModeControler', )

from os import path
from pymt import MTBoxLayout
from widgets import PresemtButton, PresemtToggleButton

class WorkModeControler(MTBoxLayout):
    def __init__(self, ctx, **kwargs):
        super(WorkModeControler, self).__init__(**kwargs)
        self.ctx = ctx
        filename = path.join(path.dirname(__file__), 'data', 'savefile.png')
        self.savebutton = PresemtButton(filename=filename, visible=False)
        self.add_widget(self.savebutton)
        self.savebutton.connect('on_release', self.ctx.save)

        self.modes = {}
        self.add_mode('edit')
        self.add_mode('layout')
        self.add_mode('live')

    def on_update(self):
        self.savebutton.visible = self.ctx.dirty
        super(WorkModeControler, self).on_update()

    def add_mode(self, mode_name):
        filename = path.join(path.dirname(__file__), 'data', '%s.png' % mode_name)
        btn = PresemtToggleButton(filename=filename)
        if mode_name == 'layout':
            btn.state = 'down'
        @btn.event
        def on_press(touch):
            for c in self.children:
                c.state = 'normal'
            btn.state = 'down'
            self.ctx.mode = mode_name
        self.add_widget(btn)
        self.modes[mode_name] = btn

    def update_state(self):
        for c in self.children:
            c.state = 'normal'
        self.modes[self.ctx.mode].state = 'down'
