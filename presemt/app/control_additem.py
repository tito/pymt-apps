from os import path
from pymt import MTBoxLayout, getCurrentTouches, gx_matrix_identity
from widgets import PresemtButton
from OpenGL.GL import *
import numpy

class AddItemMenu(MTBoxLayout):
    def __init__(self, ctx, **kwargs):
        super(AddItemMenu, self).__init__(**kwargs)
        self.ctx = ctx
        for x in self.ctx.slide_class:
            self.add_item_type(x)

    def add_item_type(self, type_factory):
        filename = path.join(path.dirname(__file__), 'data', '%s.png' %
                             type_factory.name)
        create_btn = PresemtButton(filename=filename, size=(80, 80))
        @create_btn.event
        def on_press(touch):
            touch.userdata['new_item'] = type_factory
            touch.grab(self)
        self.add_widget(create_btn)

    def on_touch_up(self, touch):
        if touch.grab_current == self and not self.collide_point(*touch.pos):
            new_item = touch.userdata['new_item'](self.ctx)
            mat = self.parent.ui_canvas.transform_mat
            mat = numpy.matrix(mat).getI()
            with gx_matrix_identity:
                glMultMatrixf(mat)
                glTranslatef(touch.x - new_item.width / 2, touch.y - new_item.height / 2, 0)
                new_item.transform_mat = glGetFloatv(GL_MODELVIEW_MATRIX)

            self.parent.ui_canvas.add_widget(new_item)
            touch.ungrab(self)

    def draw(self):
        super(AddItemMenu, self).draw()
        for touch in getCurrentTouches():
            if not self in touch.grab_list:
                continue
            with gx_matrix:
                glTranslatef(touch.x, touch.y, 0)
                touch.userdata['new_item'].draw_drag_icon()

