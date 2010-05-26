import os
import json
from pymt import *
from pymt.parser import parse_color

import euclid
from control_container import SlideContainer
from control_bookmark import BookmarkBar
from control_workmode import WorkModeControler
from control_live import LiveControler
from control_additem import AddItemMenu
from widgets import PresemtButton

css_add_keyword('grid-color', parse_color)
css_add_file(os.path.join(os.path.dirname(__file__), 'presemt.css'))
css_reload()

class Presemt(MTWidget):
    slide_class = []

    def __init__(self, **kwargs):
        super(Presemt, self).__init__(**kwargs)
        self.dirty = True
        self.filename = None
        self._mode = 'layout'
        self.current_bookmark = None
        self.interpolation = 0.0
        self.create_ui()

    @staticmethod
    def register_slide_class(type_factory):
        Presemt.slide_class.append(type_factory)

    def draw(self):
        set_color(*self.style.get('bg-color'))
        drawRectangle(pos=self.pos, size=self.size)

    def _get_mode(self):
        return self._mode
    def _set_mode(self, mode):
        self._mode = mode
        self.ui_workmode.update_state()
        if mode in ('layout', 'edit'):
            self.ui_canvas.show_grid = True
            self.ui_workmode.show()
            self.ui_bookmark.show()
            self.ui_toolbar.show()
            self.ui_saveview.show()
            self.ui_live.hide()
        else:
            self.ui_canvas.show_grid = False
            self.ui_workmode.hide()
            self.ui_bookmark.hide()
            self.ui_toolbar.hide()
            self.ui_saveview.hide()
            self.ui_live.show()
    mode = property(_get_mode, _set_mode)

    def create_ui(self):
        # create element
        self.ui_live = LiveControler(self, width=self.width, visible=False)
        self.ui_canvas = SlideContainer(self, pos=self.pos, size=self.size)
        self.ui_bookmark = BookmarkBar(self, pos=(80, self.height - 80),
                                       size=(self.width - 80, 80))
        self.ui_toolbar = AddItemMenu(self, pos=(0, 0),
                                      size=(self.width, 80))
        self.ui_workmode = WorkModeControler(self)
        self.ui_workmode.x = self.width - self.ui_workmode.width
        filename = os.path.join(os.path.dirname(__file__), 'data', 'save.png')
        self.ui_saveview = PresemtButton(filename=filename, cls='btnsave',
                                    pos=(0, self.height - 80),
                                    size=(80, 80))

        # connect
        self.ui_saveview.connect('on_release', self.save_view)

        # add to root
        self.add_widget(self.ui_canvas)
        self.add_widget(self.ui_bookmark)
        self.add_widget(self.ui_toolbar)
        self.add_widget(self.ui_saveview)
        self.add_widget(self.ui_workmode)
        self.add_widget(self.ui_live)

        # set dirty

    def set_dirty(self, *largs):
        self.dirty = True

    def set_layout_mode(self, *largs):
        self.mode = 'layout'

    def goto_previous(self, *largs):
        self.ui_bookmark.previous()

    def goto_next(self, *largs):
        self.ui_bookmark.next()

    def save_view(self, *largs):
        self.ui_bookmark.create_bookmark()
        return True

    def capture_current_view(self):
        p0 = self.ui_canvas.to_parent(0., 0.)
        p1 = self.ui_canvas.to_parent(1., 0.)
        scale = Vector(*p0).distance(p1)
        pos = self.ui_canvas.to_parent(0, 0)
        mat_trans = euclid.Matrix4()
        mat_trans[:] = self.ui_canvas.transform_mat.flatten()
        mat_trans.translate(-pos[0], -pos[1], 0)
        mat_trans.scale(1.0 / scale, 1.0 / scale, 1.0)
        return (scale, pos, euclid.Quaternion.new_rotate_matrix(mat_trans))

    def goto_view(self, bookmark):
        self.source_view = bookmark.view_transform
        self.destination_view = self.capture_current_view()
        self.current_bookmark = bookmark
        self.interpolation = 1.0

    def on_update(self):
        super(Presemt, self).on_update()
        if self.interpolation <= 0.0:
            return

        #
        # Thanks to Thomas for this fantastic code !
        #

        self.interpolation -= getFrameDt()
        if self.interpolation < 0:
            self.interpolation = 0

        i = AnimationAlpha.ease_in_out_quint(self.interpolation)
        sx, sy = self.source_view[1]
        tx, ty = self.destination_view[1]
        dx, dy = sx + i * (tx - sx), sy + i *(ty - sy)
        mat1 = euclid.Matrix4.new_translate(dx, dy, 1)

        src_scale = self.source_view[0]
        dst_scale = self.destination_view[0]
        scale = src_scale + i * (dst_scale - src_scale)
        mat2 = euclid.Matrix4.new_scale(scale, scale, 1)

        qatern = euclid.Quaternion.new_interpolate(self.source_view[2], self.destination_view[2], i)
        mat3 = qatern.get_matrix()

        mat = mat1 * mat3 * mat2

        # matrix from scatter is (4,4), matrix from euclid is (16)
        flat = self.ui_canvas.transform_mat.flatten()
        flat[:] = mat[:]
        self.ui_canvas.transform_mat = flat.reshape((4, 4))

        # finished ?
        if self.interpolation == 0 and self.current_bookmark:
            self.ui_bookmark.update_screenshot(self.current_bookmark)
            self.current_bookmark = None

    def save(self, *largs):
        data = {}
        data['view'] = self.ui_canvas.state
        data['bookmark'] = self.ui_bookmark.state
        data['items'] = [x.state for x in self.ui_canvas.children]
        data = json.dumps(data)
        filename = self.filename
        if filename is None:
            print data
        else:
            with open(filename, 'w') as fd:
                fd.write(data)
        self.dirty = False

    def load(self, filename):
        self.filename = filename
        data = None
        try:
            with open(filename, 'r') as fd:
                data = fd.read()
        except:
            return
        data = json.loads(data)
        if data is None:
            return

        # load view
        view = data.get('view', None)
        if view:
            self.ui_canvas.state = view

        # load bookmark
        bookmark = data.get('bookmark', None)
        if bookmark:
            self.ui_bookmark.state = bookmark

        # load items
        for x in data.get('items', []):
            name = x.get('name', None)
            if name is None:
                continue
            # search the item in the factory 
            slide = None
            for slide_class in Presemt.slide_class:
                if slide_class.name == name:
                    slide = slide_class(self)
            if slide is None:
                print 'Unable to found Slide with name = ', name
                continue
            slide.state = x
            self.ui_canvas.add_widget(slide)

        self.dirty = False


#
# register slide type, after presemt
#
from slide_text import SlideText
from slide_image import SlideImage
from slide_video import SlideVideo

Presemt.register_slide_class(SlideText)
Presemt.register_slide_class(SlideImage)
Presemt.register_slide_class(SlideVideo)


if __name__ == "__main__":
    # create a fullscreen presemt
    s = Presemt(size=getWindow().size)
    runTouchApp(s)

