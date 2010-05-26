import numpy
import os
from pymt import *
from slideitems import *
from euclid import Matrix4

def get_screen_texture(mode='front'):
    from OpenGL.GL import glReadBuffer, glReadPixels, GL_RGB, \
            GL_UNSIGNED_BYTE, GL_FRONT, GL_BACK
    win = getWindow()
    if mode.lower() == 'back':
        glReadBuffer(GL_BACK)
    else:
        glReadBuffer(GL_FRONT)
    data = glReadPixels(0, 0, win.width, win.height, GL_RGB, GL_UNSIGNED_BYTE)
    tex = Texture.create(win.width, win.height, GL_RGB, rectangle=True)
    tex.blit_buffer(data)
    return tex

class PresemtButton(MTImageButton):
    def draw(self):
        super(MTImageButton, self).draw()
        super(PresemtButton, self).draw()

class PresemtToggleButton(PresemtButton):
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if self.state == 'down':
            self.state = 'normal'
        else:
            self.state = 'down'
        self.dispatch_event('on_press', touch)
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if not touch.grab_current == self:
            return False
        touch.ungrab(self)
        self.state = self.state
        if self.collide_point(*touch.pos):
            self.dispatch_event('on_release', touch)
        return True

class BackgroundGrid(MTScatterPlane):
    def __init__(self, **kwargs):
        super(BackgroundGrid, self).__init__(**kwargs)
        self.show_grid = True

        self.grid_dl = GlDisplayList()
        with self.grid_dl:
            set_color(*presentation.grid_color)
            glLineWidth(1)
            for i in range(-1000,1000):
                drawLine((i*50, -50000, i*50, 50000))
                drawLine((-50000, i*50, 50000, i*50))

    def draw(self):
        if self.show_grid:
            self.grid_dl.draw()

class ViewBookMark:
    def __init__(self, transform, **kwargs):
        self.view_transform = transform
        self.screenshot = Image(get_screen_texture())
        self.updated = False

class BookmarkBar(MTBoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('spacing',2)
        kwargs.setdefault('padding',4)
        super(BookmarkBar, self).__init__(**kwargs)
        self.bookmarks_buttons = {}
        self._current = None

    def add_bookmark(self, bookmark):
        bookmark_btn = MTImageButton(image=bookmark.screenshot, scale=0.1)
        @bookmark_btn.event
        def on_press(touch):
            if presentation.edit_mode in ('layout', 'edit') and touch.is_double_tap:
                self.remove_widget(bookmark_btn)
                del self.bookmarks_buttons[bookmark]
            else:
                self.parent.goto_view(bookmark)
            return True

        self.bookmarks_buttons[bookmark] = bookmark_btn
        self.add_widget(bookmark_btn)
        self.do_layout()
        self._current = bookmark

    def update_screenshot(self, bookmark):
        if not bookmark in self.bookmarks_buttons:
            return
        bookmark.screenshot = Image(get_screen_texture())
        self.bookmarks_buttons[bookmark].image = bookmark.screenshot

    def previous(self):
        try:
            k = self.bookmarks_buttons.keys()
            idx = (k.index(self._current) - 1) % len(self.bookmarks_buttons)
            print idx
            self._current = k[idx]
            self.parent.goto_view(self._current)
        except:
            pass

    def next(self):
        try:
            k = self.bookmarks_buttons.keys()
            idx = (k.index(self._current) + 1) % len(self.bookmarks_buttons)
            print idx
            self._current = k[idx]
            self.parent.goto_view(self._current)
        except:
            pass

class AddItemMenu(MTBoxLayout):
    def __init__(self, **kwargs):
        super(AddItemMenu, self).__init__(**kwargs)
        self.add_item_type('text', SlideText)
        self.add_item_type('image', SlideImage)
        self.add_item_type('video', SlideVideo)
        self.add_item_type('graph', SlideTracer)

    def add_item_type(self, name, type_factory):
        filename = os.path.join(os.path.dirname(__file__), 'data', '%s.png' % name)
        create_btn = PresemtButton(filename=filename, size=(80, 80))
        @create_btn.event
        def on_press(touch):
            print 'GRAB', type_factory, self
            touch.userdata['new_item'] = type_factory
            touch.grab(self)
        self.add_widget(create_btn)

    def on_touch_up(self, touch):
        if touch.grab_current == self and not self.collide_point(*touch.pos):
            new_item = touch.userdata['new_item']()
            mat = self.parent.ui_canvas.transform_mat
            mat = numpy.matrix(mat).getI()
            with gx_matrix_identity:
                glMultMatrixf(mat)
                glTranslated(touch.x - new_item.width / 2, touch.y - new_item.height / 2, 0)
                new_item.transform_mat = glGetFloatv(GL_MODELVIEW_MATRIX)

            self.parent.ui_canvas.add_widget(new_item)
            touch.ungrab(self)

    def draw(self):
        super(AddItemMenu, self).draw()
        for touch in getAvailableTouchs():
            if not self in touch.grab_list:
                continue
            with gx_matrix:
                glTranslated(touch.x, touch.y, 0)
                touch.userdata['new_item'].draw_drag_icon()

class WorkModeControler(MTBoxLayout):
    def __init__(self, **kwargs):
        super(WorkModeControler, self).__init__(**kwargs)
        self.modes = {}
        self.add_mode('edit')
        self.add_mode('layout')
        self.add_mode('live')

    def add_mode(self, mode_name):
        filename = os.path.join(os.path.dirname(__file__), 'data', '%s.png' % mode_name)
        btn = PresemtToggleButton(filename=filename)
        if mode_name == 'layout':
            btn.state = 'down'
        @btn.event
        def on_press(touch):
            for c in self.children:
                c.state = 'normal'
            btn.state = 'down'
            presentation.edit_mode = mode_name
            self.parent.mode = mode_name
        self.add_widget(btn)
        self.modes[mode_name] = btn

    def update_state(self):
        for c in self.children:
            c.state = 'normal'
        self.modes[presentation.edit_mode].state = 'down'

class LiveControler(MTBoxLayout):
    def __init__(self, root, **kwargs):
        super(LiveControler, self).__init__(**kwargs)
        filename = os.path.join(os.path.dirname(__file__), 'data', 'settings.png')
        self.settings = PresemtButton(filename=filename)
        filename = os.path.join(os.path.dirname(__file__), 'data', 'previous.png')
        self.previous = PresemtButton(filename=filename)
        filename = os.path.join(os.path.dirname(__file__), 'data', 'next.png')
        self.next = PresemtButton(filename=filename)

        self.settings.connect('on_release', root.set_layout_mode)
        self.previous.connect('on_release', root.goto_previous)
        self.next.connect('on_release', root.goto_next)

        self.add_widget(self.previous)
        self.add_widget(self.next)
        self.add_widget(MTWidget(size_hint=(1, 1)))
        self.add_widget(self.settings)

