from slide import SlideItem
from pymt import MTTextInput

class SlideText(SlideItem):
    name = 'text'
    def __init__(self, *largs, **kwargs):
        kwargs.setdefault('do_rotation', False)
        super(SlideText, self).__init__(*largs, **kwargs)
        self.text_input = MTTextInput(
            label='Text...', cls='slide-textinput',
            autosize=True, group='presemt-textinput')
        self.text_input.connect('on_resize', self.resize)
        self.add_widget(self.text_input)
        self.resize()
        self.text_input.connect('on_text_change', self.ctx.set_dirty)

    def resize(self, *l):
        self.width = self.text_input.width

    def _get_state(self):
        d = super(SlideText, self)._get_state()
        d['label'] = self.text_input.label
        return d

    def _set_state(self, state):
        super(SlideText, self)._set_state(state)
        self.text_input.label = state.get('label')

