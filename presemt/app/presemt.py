import os
import time
import json
from pymt import *
from pymt.lib.transformations import *
from pymt.parser import parse_color

import euclid
from control_container import SlideContainer
from control_bookmark import BookmarkBar, get_screen_texture
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
        self._filebrowser = None
        self._filebrowser_cb = None
        self.current_bookmark = None
        self.interpolation = 0.0
        self.create_ui()

    @staticmethod
    def register_slide_class(type_factory):
        Presemt.slide_class.append(type_factory)

    def _filebrowser_select(self, files, *largs):
        if self._filebrowser_cb is None:
            return
        if not len(files):
            return
        filename = files[0]
        if os.path.isdir(filename):
            return
        self._filebrowser_cb(filename)

    def _filebrowser_touch(self, touch):
        if not self._filebrowser.collide_point(*touch.pos):
            self.close_filebrowser()

    def is_filebrowser_open(self):
        if self._filebrowser is None:
            return False
        return self._filebrowser in self.children

    def close_filebrowser(self):
        if self._filebrowser is None:
            return
        self.remove_widget(self._filebrowser)
        self._filebrowser_cb = None

    def open_filebrowser(self, callback, filters=[]):
        if self._filebrowser is None:
            self._filebrowser = MTFileBrowserView(pos=(0, 80),
                    size=(350, getWindow().height - 160))
            self._filebrowser.path = '.'
            self._filebrowser.connect('on_selection_change', self._filebrowser_select)
            self._filebrowser.connect('on_touch_down', self._filebrowser_touch)
        self.remove_widget(self._filebrowser)
        self.add_widget(self._filebrowser)
        self._filebrowser.filters = filters
        self._filebrowser_cb = callback
        self._filebrowser.update()
        return self._filebrowser

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
        #current view = translation, scale and rotation around(0,0)
        #we store quaternion, becasue it is much better for interpolating angles (always rotates shortest way)
        scale = self.ui_canvas.scale
        pos = Vector(*self.ui_canvas.to_parent(0, 0))
        quat = quaternion_from_matrix(self.ui_canvas.transform)
        return (scale, pos, quat)

    def goto_view(self, bookmark):
        self.source_view = self.capture_current_view()
        self.destination_view = bookmark.view_transform
        self.current_bookmark = bookmark
        self.interpolation = 1.0

    def on_update(self):
        super(Presemt, self).on_update()
        if self.interpolation <= 0.0:
            return
        
        self.interpolation -= getFrameDt()
        if self.interpolation < 0:
            self.interpolation = 0
    
        #i goes from 0.0 to 1.0
        i = AnimationAlpha.ease_in_out_quint(abs(1.0-self.interpolation))
        
        #create interpolated scale, translation and rotation matrix from saved state
        s = self.source_view[0] + i * (self.destination_view[0] - self.source_view[0])
        scale = scale_matrix(s)

        t = self.source_view[1] + i*(self.destination_view[1] - self.source_view[1] )
        translate = translation_matrix((t.x, t.y, 0))

        q = quaternion_slerp(self.source_view[2], self.destination_view[2], i)
        rotate = quaternion_matrix(q)
    
        #combine the three matrices to get the transform for teh current interpolation value
        mat = concatenate_matrices(translate,rotate,scale)
        self.ui_canvas.transform = mat

        # finished ?
        if self.interpolation == 0 and self.current_bookmark:
            self.ui_bookmark.update_screenshot(self.current_bookmark)
            self.current_bookmark = None

    def export_to_pdf(self):
        def _screenshot():
            # method imported from keybinding screenshot
            import pygame
            from OpenGL.GL import glReadBuffer, glReadPixels, GL_RGB, \
                GL_UNSIGNED_BYTE, GL_BACK, GL_FRONT
            win = getWindow()
            glReadBuffer(GL_FRONT)
            data = glReadPixels(0, 0, win.width, win.height, GL_RGB, GL_UNSIGNED_BYTE)
            surface = pygame.image.fromstring(str(buffer(data)), win.size, 'RGB', True)
            filename = 'presemt.screenshot.tmp.jpg'
            pygame.image.save(surface, filename)
            return filename

        # create PDF !
        from reportlab.pdfgen import canvas

        # do capture in live mode
        self.mode = 'live'
        self.remove_widget(self.ui_live)

        # create a pdf with the same name as our filename
        filename = '%s.pdf' % ('.'.join(self.filename.split('.')[:-1]))
        pdf = canvas.Canvas(filename, pagesize=getWindow().size)

        # prepare pymt to run in slave mode
        runTouchApp(self, slave=True)
        evloop = getEventLoop()

        # ensure the window have the good size
        getWindow().dispatch_event('on_resize', *getWindow().size)

        # wait loader to finished
        print 'Wait loader to finish to load all childrens'
        for x in self.ui_canvas.children:
            if not x.is_loaded:
                time.sleep(.1)
                evloop.idle()

        # capture all bookmark
        last_screenshot = None
        for bookmark in self.ui_bookmark.bookmarks_keys:
            # XXX called 2 times to be sure that translation is done
            self.goto_view(bookmark)
            self.interpolation = 0.0000001

            # call idle twice
            evloop.idle()
            evloop.idle()

            # put image on pdf
            last_screenshot = _screenshot()
            pdf.drawInlineImage(last_screenshot, 0, 0)
            pdf.showPage()
            os.unlink(last_screenshot)

        # save pdf
        pdf.save()
        print
        print 'PDF saved to', filename
        print


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
                    slide = slide_class(self, restoremode=True)
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

