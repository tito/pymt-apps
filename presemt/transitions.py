from pymt import *
from pyglet.gl import *

class SlideTransition(MTWidget):
    
    def __init__(self, presentation, src, dest, **kwargs):
        super(SlideTransition, self).__init__(**kwargs)
        self.presentation = presentation
        self.src = src
        self.dest = dest
        self.progress = 0.0
        self.frames = 30

        self.src_fbo  = Fbo(size=(self.presentation.width, self.presentation.height))
        with self.src_fbo:
            glClear(GL_COLOR_BUFFER_BIT)
            self.src.on_draw()
        
        self.dest_fbo = Fbo(size=(self.presentation.width, self.presentation.height))
        with self.dest_fbo:
            glClear(GL_COLOR_BUFFER_BIT)
            self.dest.on_draw()
        
        
    def draw(self):
        if self.progress < 1.0:
            with gx_matrix:
                self.draw_transition(self.progress)
            self.progress += 1.0/self.frames
        else:
            self.presentation.current_slide = self.dest


    def draw_transition(self, t):
        set_color(1,1,1)
        glTranslated(0-t*self.presentation.width, 0,0)
        drawTexturedRectangle(self.src_fbo.texture, size=self.presentation.size)
        glTranslated(self.presentation.width, 0,0)
        drawTexturedRectangle(self.dest_fbo.texture, size=self.presentation.size)