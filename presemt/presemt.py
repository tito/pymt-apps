from pymt import *
from pyglet.gl import *
import pyglet


#local imports
import presentation
from slides import *
from transitions import *


class SlideShow(MTWidget):
    
    def __init__(self, **kwargs):
        presentation.root = self
        super(SlideShow, self).__init__(**kwargs)
        self.slides = []
        self._current_slide = None

    def add_widget(self, widget, front=True):
        self.slides.append(widget)
        widget.parent = self
        if not self.current_slide:
            self.current_slide = widget    

    def on_update(self):
        self.size = (1366,768)
        super(SlideShow, self).on_update()
        
    def draw(self):
        glClearColor(*presentation.bg_color)
        glClear(GL_COLOR_BUFFER_BIT)
           
    def next_slide(self, touch=None):
        next_slide_index = (self.slides.index(self.current_slide)+1) % len(self.slides)
        self.current_slide = SlideTransition(self, self.current_slide, self.slides[next_slide_index])

    def set_current_slide(self, slide):
        self._current_slide = slide
        self.children = [self._current_slide ]
    def get_current_slide(self):
        return self._current_slide 
    current_slide = property(get_current_slide, set_current_slide, doc='The currently active slide')




if __name__ == "__main__":
    w = MTWindow()
    s = SlideShow()
    s.add_widget(ScatterSlide())
    w.add_widget(s)
    runTouchApp()

