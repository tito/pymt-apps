from slide import SlideItem
from pymt import MTTextArea

class SlideText(SlideItem):
    name = 'text'
    def __init__(self, *largs, **kwargs):
        kwargs.setdefault('do_rotation', False)
        super(SlideText, self).__init__(*largs, **kwargs)
        self.textarea = MTTextArea(
            label='Text...', cls='slide-textinput',
            autosize=True, group='presemt-textinput')
        self.textarea.connect('on_resize', self.resize)
        self.add_widget(self.textarea)
        self.resize()
        self.textarea.connect('on_text_change', self.ctx.set_dirty)

    def _on_text_change(self, *args):
        self.ctx.set_dirty()
        self.resize()

    def resize(self, *args):
        self.size = self.textarea.size

    def _get_state(self):
        d = super(SlideText, self)._get_state()
        d['label'] = self.textarea.value
        return d
    def _set_state(self, state):
        super(SlideText, self)._set_state(state)
        self.textarea.value = state.get('label')
    state = property(_get_state, _set_state)

