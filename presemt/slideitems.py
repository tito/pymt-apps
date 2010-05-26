from pymt import *
from OpenGL.GL import *
import presentation


class EditProxy(MTWidget):

    def on_touch_down(self, touch):
        if not presentation.edit_mode == 'layout':
            return super(EditProxy, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if not presentation.edit_mode == 'layout':
            return super(EditProxy, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if not presentation.edit_mode == 'layout':
            return super(EditProxy, self).on_touch_up(touch)


class SlideItem(MTScatterWidget):

    def __init__(self, **kwargs):
        self.link = None
        self.locked = True
        self.proxy = EditProxy()
        super(SlideItem, self).__init__(**kwargs)
        super(SlideItem, self).add_widget(self.proxy)

    def add_widget(self, widget, front=True):
        self.proxy.add_widget(widget, front)

    def draw(self):
        if presentation.edit_mode == 'layout':
            set_color(0,1,0)
            drawRectangle(pos=(-10,-10),size=(self.width+20,self.height+20))
        if presentation.edit_mode == 'edit':
            set_color(1,1,0)
            drawRectangle(pos=(-10,-10),size=(self.width+20,self.height+20))
        if self.link:
            set_color(0,0,1)
            drawRectangle(pos=(-4,-4),size=(self.width+8,self.height+8))

    @staticmethod
    def draw_drag_icon(self=None):
        set_color(1,0,1)
        drawRectangle(pos=(-30,-30),size=(60,60))

    def on_touch_down(self, touch):
        if presentation.edit_mode == 'layout' and touch.is_double_tap \
           and self.collide_point(*touch.pos):
            self.parent.remove_widget(self)
            return True
        if not (presentation.edit_mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if not (presentation.edit_mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if not (presentation.edit_mode == 'live' and self.locked):
            return super(SlideItem, self).on_touch_up(touch)

class SlideText(SlideItem):
    def __init__(self, **kwargs):
        kwargs.setdefault('do_rotation', False)
        super(SlideText, self).__init__(**kwargs)
        self.text_input = MTTextInput(label='Text...',
                                      cls='slide-textinput',
                                      autosize=True,
                                      group='presemt-textinput')
        self.text_input.connect('on_resize', self.resize)
        self.add_widget(self.text_input)
        self.resize()

    def resize(self, *l):
        self.width = self.text_input.width


class SlideImage(SlideItem):
    def __init__(self, **kwargs):
        super(SlideImage, self).__init__(**kwargs)
        self.image = Image('content/1.png')
        self.width = (self.image.width/float(self.image.height)) * self.height

    def draw(self):
        super(SlideImage, self).draw()
        self.image.size = self.size
        self.image.draw()

    def on_touch_down(self, touch):
        if presentation.edit_mode == 'edit' and self.collide_point(*touch.pos):
            fb = MTFileBrowser(pos =(100,100))
            fb.push_handlers(on_select=self.load_file)
            self.get_root_window().add_widget(fb)
            return True
        else:
            return super(SlideImage, self).on_touch_down(touch)

    def load_file(self, files):
        self.image = Image(files[0])




class SlideVideo(SlideItem):
    def __init__(self, **kwargs):
        super(SlideVideo, self).__init__(**kwargs)
        self.video = MTVideo(filename='content/softboy.avi',pos=(0,0),on_playback_end='loop',volume=0.1)
        self.width = (self.video.width/float(self.video.height)) * self.height

    def draw(self):
        super(SlideVideo, self).draw()
        self.size = self.video.size
        self.video.draw()

    def on_touch_down(self, touch):
        if presentation.edit_mode == 'edit' and self.collide_point(*touch.pos):
            fb = MTFileBrowser()
            fb.push_handlers(on_select=self.load_file)
            self.get_root_window().add_widget(fb)
            return True
        else:
            return super(SlideVideo, self).on_touch_down(touch)

    def load_file(self, files):
        self.video = MTVideo(filename=files[0],pos=(0,0),on_playback_end='loop',volume=0.1)




from untangle import GraphUI

class SlideTracer(SlideItem):
    def __init__(self, **kwargs):
        super(SlideTracer, self).__init__(**kwargs)
        self.size = (600,600)
        self.locked = False
        self.tracer = GraphUI(10)
        self.add_widget(self.tracer)

