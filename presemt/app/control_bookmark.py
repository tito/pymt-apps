__all__ = ('ViewBookMark', 'BookmarkBar')

import pygame
from pymt import MTImageButton, Image, getWindow, Texture, \
        serialize_numpy, deserialize_numpy, MTKineticList, MTKineticItem
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


class ViewBookMark(MTImageButton, MTKineticItem):
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
            self.image = Image(tex)
        kwargs['image'] = self.image
        self.updated = False
        super(ViewBookMark, self).__init__(**kwargs)

    def on_press(self, touch):
        p = self.parent
        if p.ctx.mode in ('layout', 'edit') and touch.is_double_tap:
            p.remove_bookmark(self)
        else:
            p.goto(p.bookmarks.index(self))
        return True

    def update_screenshot(self):
        tex, info = get_screen_texture()
        self.info = info
        self.info[-1] = b64encode(self.info[-1])
        self.image = Image(tex)


class BookmarkBar(MTKineticList):
    def __init__(self, ctx, **kwargs):
        kwargs.setdefault('spacing', 2)
        kwargs.setdefault('padding', 4)
        kwargs.setdefault('h_limit', 1)
        kwargs.setdefault('do_y', False)
        kwargs.setdefault('title', None)
        kwargs.setdefault('deletable', False)
        kwargs.setdefault('searchable', False)
        kwargs.setdefault('w_limit', 0)
        kwargs.setdefault('do_x', True)
        kwargs.setdefault('do_y', False)
        super(BookmarkBar, self).__init__(**kwargs)
        self.ctx = ctx
        self.bookmarks = []
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
        self.bookmarks.append(bookmark)
        self.add_widget(bookmark)
        self.do_layout()
        self._current = bookmark

    def remove_bookmark(self, bookmark):
        self.remove_widget(bookmark)
        # remove current, set to next
        if self._current == bookmark:
            self.next()
        self.bookmarks.remove(bookmark)

    def update_screenshot(self, bookmark):
        if not bookmark in self.bookmarks:
            return
        bookmark.update_screenshot()

    def goto(self, idx):
        try:
            self._current = self.bookmarks[idx % len(self.bookmarks)]
            self.parent.goto_view(self._current)
        except:
            pass

    def previous(self):
        if self._current is None:
            return
        self.goto(self.bookmarks.index(self._current) - 1)

    def next(self):
        if self._current is None:
            return
        self.goto(self.bookmarks.index(self._current) + 1)

    def _get_state(self):
        data = []
        for x in self.bookmarks:
            data.append({
                'matrix': serialize_numpy(x.view_transform),
                'info': x.info
            })
        return data
    def _set_state(self, state):
        for x in state:
            bookmark = ViewBookMark(deserialize_numpy(x.get('matrix')),
                                    info=x.get('info'))
            self.add_bookmark(bookmark)
    state = property(_get_state, _set_state)
