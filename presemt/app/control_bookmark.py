__all__ = ('ViewBookMark', 'BookmarkBar')

import pygame
from pymt import MTBoxLayout, MTImageButton, Image, getWindow, Texture, \
        serialize_numpy, deserialize_numpy, MTList
from OpenGL.GL import glReadBuffer, glReadPixels, GL_RGB, \
        GL_UNSIGNED_BYTE, GL_FRONT, GL_BACK
from base64 import b64encode, b64decode

def get_screen_texture(mode='back'):
    win = getWindow()
    if mode.lower() == 'front':
        glReadBuffer(GL_FRONT)
    else:
        glReadBuffer(GL_BACK)
    data = glReadPixels(0, 0, win.width, win.height, GL_RGB, GL_UNSIGNED_BYTE)

    # do a mini
    size = win.width / 10, win.height / 10
    surf = pygame.image.fromstring(data, win.size, 'RGB')
    surf = pygame.transform.scale(surf, size)
    data = pygame.image.tostring(surf, 'RGB')

    tex = Texture.create(size[0], size[1], GL_RGB, rectangle=True)
    tex.blit_buffer(data)
    return tex, [size[0], size[1], data]


class ViewBookMark:
    def __init__(self, transform, **kwargs):
        kwargs.setdefault('info', None)
        self.view_transform = transform

        info = kwargs.get('info')
        if info is None:
            self.update_screenshot()
        else:
            self.info = info
            w, h, data = self.info
            data = b64decode(data)
            tex = Texture.create(w, h, GL_RGB, GL_UNSIGNED_BYTE)
            tex.blit_buffer(data)
            self.screenshot = Image(tex)
        self.updated = False

    def update_screenshot(self):
        tex, info = get_screen_texture()
        self.info = info
        self.info[-1] = b64encode(self.info[-1])
        self.screenshot = Image(tex)

class BookmarkBar(MTList):
    def __init__(self, ctx, **kwargs):
        kwargs.setdefault('do_y', False)
        super(BookmarkBar, self).__init__(**kwargs)
        self.ctx = ctx
        self.layout = MTBoxLayout(spacing=2, padding=4)
        self.add_widget(self.layout)
        self.bookmarks_buttons = {}
        self.bookmarks_keys = []
        self._current = None

    def create_bookmark(self):
        self.add_bookmark(ViewBookMark(self.ctx.capture_current_view()))

    def on_touch_down(self, touch):
        ret = super(BookmarkBar, self).on_touch_down(touch)
        if self.collide_point(*touch.pos):
            return True
        return ret

    def on_touch_move(self, touch):
        ret = super(BookmarkBar, self).on_touch_move(touch)
        if self.collide_point(*touch.pos):
            return True
        return ret

    def on_touch_up(self, touch):
        ret = super(BookmarkBar, self).on_touch_up(touch)
        if self.collide_point(*touch.pos):
            return True
        return ret

    def add_bookmark(self, bookmark):
        bookmark_btn = MTImageButton(image=bookmark.screenshot)
        @bookmark_btn.event
        def on_press(touch):
            if self.ctx.mode in ('layout', 'edit') and touch.is_double_tap:
                self.layout.remove_widget(bookmark_btn)
                # remove current, set to next
                if self._current == bookmark:
                    self.next()
                del self.bookmarks_buttons[bookmark]
                self.bookmarks_keys.remove(bookmark)
            else:
                self.goto(self.bookmarks_keys.index(bookmark))
            return True

        self.bookmarks_buttons[bookmark] = bookmark_btn
        self.bookmarks_keys.append(bookmark)
        self.layout.add_widget(bookmark_btn)
        self.layout.do_layout()
        self._current = bookmark

    def update_screenshot(self, bookmark):
        if not bookmark in self.bookmarks_buttons:
            return
        bookmark.update_screenshot()
        self.bookmarks_buttons[bookmark].image = bookmark.screenshot

    def goto(self, idx):
        try:
            self._current = self.bookmarks_keys[idx % len(self.bookmarks_keys)]
            self.parent.goto_view(self._current)
        except:
            pass

    def previous(self):
        if self._current is None:
            return
        self.goto(self.bookmarks_keys.index(self._current) - 1)

    def next(self):
        if self._current is None:
            return
        self.goto(self.bookmarks_keys.index(self._current) + 1)

    def _get_state(self):
        data = []
        for x in self.bookmarks_keys:
            data.append({
                'scale': x.view_transform[0],
                'pos': x.view_transform[1],
                'quat': serialize_numpy(x.view_transform[2]),
                'info': x.info
            })
        return data
    def _set_state(self, state):
        for x in state:
            bookmark = ViewBookMark(None, info=x.get('info'))
            bookmark.view_transform = (x.get('scale'), x.get('pos'),
                                       deserialize_numpy(x.get('quat')))
            self.add_bookmark(bookmark)
    state = property(_get_state, _set_state)
