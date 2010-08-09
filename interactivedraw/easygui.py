'''
EasyGui: an easy way to make UI with PyMT

NO CHANGE IS ALLOWED ON THIS FILE, WITHOUT THE AUTHOR APPROVAL.

@author Mathieu Virbel <tito@bankiz.org>
'''

from pymt import *

easygui_css = '''
easygui {
    draw-background: 1;
    bg-color: rgba(30, 30, 30, 255);
}

easyguilabel {
    font-size: 11;
    color: rgb(200, 200, 200);
}

easyguicheckbox {
    draw-alpha-background: 0;
    draw-border: 0;
    bg-color-down: rgb(0, 125, 200);
}

easyguislider {
    slider-color: rgb(0, 125, 200);
    draw-slider-alpha-background: 0;
}

easyguipaneltitle {
    draw-alpha-background: 0;
    draw-border: 0;
    bg-color-down: rgb(0, 125, 200);
    bg-color: rgb(100, 100, 100);
}
'''

css_add_sheet(easygui_css)

class EasyGuiPanelTitle(MTToggleButton):
    def __init__(self, **kwargs):
        kwargs.setdefault('autowidth', True)
        kwargs.setdefault('size', (50, 25))
        super(EasyGuiPanelTitle, self).__init__(**kwargs)

class EasyGuiCheckBox(MTToggleButton):
    def __init__(self, **kwargs):
        kwargs.setdefault('size', (25, 25))
        super(EasyGuiCheckBox, self).__init__(**kwargs)

class EasyGuiSlider(MTSlider):
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        super(EasyGuiSlider, self).__init__(**kwargs)

class EasyGuiLabel(MTLabel):
    pass

class EasyGui(MTBoxLayout):
    '''EasyGui, a way to contruct fast UI ::

        g = EasyGui('Settings', size=(200, 200))
        g.panel('Min/Max')
        g.add_slider('Maximum', 'MAX', 60)
        g.add_slider('Minimum', 'MIN', 20)
        g.panel('Other')
        g.add_toggle('Save at exit', 'SAVE', False)

    :Parameters:
        `title`: str, default to "EasyGui"
            Default title of the GUI

    :Events:
        `on_change`: key, value
            Fired when a value change in the GUI
    '''
    easygui_id = 0
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('mode', 'oneline')
        super(EasyGui, self).__init__(**kwargs)
        EasyGui.easygui_id += 1
        self._guid = 'easygui%d' % EasyGui.easygui_id
        self._title = kwargs.get('title', 'EasyGui')
        self._values = {}
        self._keys = {}
        self._panels = {}
        self._current = None
        self._titles = MTBoxLayout(size_hint=(1, None))
        self.mode = kwargs.get('mode')
        self.label_width = 100
        self.panel('default')
        self.register_event_type('on_change')
        self.add_widget(self._titles)

    def on_change(self, key, value):
        pass

    @property
    def title(self):
        return self._title

    @property
    def values(self):
        return self._values
    
    def panel(self, title):
        if self._current is not None:
            self.remove_widget(self._current)
        create = False
        if not title in self._panels:
            self._panels[title] = MTBoxLayout(orientation='vertical')
            create = True
        self._current = self._panels[title]
        self.add_widget(self._current)
        if title == 'default':
            return
        if not create:
            return
        def select_panel(*largs):
            self.panel(title)
        btitle = EasyGuiPanelTitle(label=' %s ' % title, group=self._guid)
        btitle.connect('on_press', select_panel)
        self._titles.add_widget(btitle)
        self._titles.visible = len(self._titles.children) > 1

    def toggle(self, title, key, default=True):
        control = EasyGuiCheckBox()
        if self.mode == 'oneline':
            control.size_hint = (None, 1)
        def _get():
            return control.state == 'down'
        def _set(x):
            if x:
                control.state = 'down'
            else:
                control.state = 'normal'
        def _change(*largs):
            self._change(key, control.state == 'down')
        control.connect('on_press', _change)
        control.connect('on_release', _change)
        self._add_control(title, key, default, control, _get, _set)

    def slider(self, title, key, default=0, min=0, max=100):
        control = EasyGuiSlider(value=default, min=min, max=max)
        control.size_hint = (1, None)
        def _get():
            return control.value
        def _set(x):
            control.value = x
        def _change(*largs):
            self._change(key, control.value)
        control.connect('on_value_change', _change)
        self._add_control(title, key, default, control, _get, _set)

    def _change(self, key, value):
        if key in self._values and self._values[key] == value:
            return
        self._values[key] = value
        self.dispatch_event('on_change', key, value)

    def _add_control(self, title, key, default, control, _get, _set):
        self._keys[key] = (control, _get, _set)
        label = EasyGuiLabel(
            label=title, padding_x=10,
            size=(self.label_width, 30),
            anchor_y='middle')

        if len(self._current.children):
            self._current.remove_widget(self._current.children[0])
        if self.mode == 'oneline':
            label.size_hint = (None, 1)
            m = MTBoxLayout(size_hint=(1, None), height=30)
            m.add_widget(label)
            m.add_widget(control)
            self._current.add_widget(m)
        else:
            label.size_hint = (1, None)
            self._current.add_widget(label)
            self._current.add_widget(control)
        self._current.add_widget(MTWidget(size_hint=(None, 1)))

        self.do_layout()

        # set default value
        _set(default)
        self._change(key, default)

if __name__ == '__main__':
    gui = EasyGui(size_hint=(None, None), size=(400, 200))
    gui.panel('Control 1')
    gui.toggle('Toggle 1', 'bleh')
    gui.toggle('Toggle 2', 'bleh2')
    gui.slider('Slider 1', 'slide1', default=50)
    gui.slider('Slider 2', 'slide2')
    gui.panel('Second')
    gui.toggle('bleh', 'azdpok')

    g = MTScatterWidget(size=gui.size, do_scale=0)
    g.add_widget(gui)
    runTouchApp(g)
