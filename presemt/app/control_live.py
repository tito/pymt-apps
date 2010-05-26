__all__ = ('LiveControler', )

from os import path
from pymt import MTBoxLayout, MTWidget
from widgets import PresemtButton

class LiveControler(MTBoxLayout):
    def __init__(self, ctx, **kwargs):
        super(LiveControler, self).__init__(**kwargs)
        filename = path.join(path.dirname(__file__), 'data', 'settings.png')
        self.settings = PresemtButton(filename=filename)
        filename = path.join(path.dirname(__file__), 'data', 'previous.png')
        self.previous = PresemtButton(filename=filename)
        filename = path.join(path.dirname(__file__), 'data', 'next.png')
        self.next = PresemtButton(filename=filename)

        self.settings.image.opacity = .3
        self.previous.image.opacity = .3
        self.next.image.opacity = .3

        self.settings.connect('on_release', ctx.set_layout_mode)
        self.previous.connect('on_release', ctx.goto_previous)
        self.next.connect('on_release', ctx.goto_next)

        self.add_widget(self.previous)
        self.add_widget(self.next)
        self.add_widget(MTWidget(size_hint=(1, 1)))
        self.add_widget(self.settings)

