'''
    MTYoutube, a multitouch youtube browser based on PyMT
    Copyright (C) 2009  Mathieu Virbel <tito@bankiz.org>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

'''

from pymt import *
from OpenGL.GL import *
from youtubedl import *
import threading
import collections
import os
import urllib
import hashlib
import random
import sqlite3
import math
import time

class YoutubeSearcher(threading.Thread):
    def __init__(self, keyword):
        super(YoutubeSearcher, self).__init__()
        self.queue = collections.deque()
        self.daemon = True
        self.keyword = keyword
        self.quit = False

    def _get_cache(self):
        current_path = '.'#os.path.dirname(sys.modules[__name__].__file__)
        cache_path = os.path.join(current_path, 'cache')
        if not os.path.exists(cache_path):
            os.mkdir(cache_path)
        return cache_path

    def _download_thumbnail(self, url):
        cache_path = self._get_cache()
        id = hashlib.sha224(url).hexdigest() + '.' + url.split('.')[-1]
        image_path = os.path.join(cache_path, id)
        if os.path.exists(image_path):
            return image_path

        data = urllib.urlopen(url).read()
        fd = open(image_path, 'wb')
        fd.write(data)
        fd.close()

        return image_path

    def _get_flventries(self, url):
        cache_path = self._get_cache()
        database_path = os.path.join(cache_path, 'flv.db')
        if not hasattr(self, '_conn'):
            if not os.path.exists(database_path):
                self._conn = sqlite3.connect(database_path)
                c = self._conn.cursor()
                c.execute('create table flv ( watch text, type text, url text )')
                self._conn.commit()
                c.close()
            else:
                self._conn = sqlite3.connect(database_path)

        c = self._conn.cursor()
        c.execute('select type, url from flv where watch=?', (url, ))
        rows = c.fetchall()
        if len(rows):
            c.close()
            return rows

        urls = YoutubeGetFlv(url)
        if urls is None:
            return None

        for flv in urls:
            c.execute('insert into flv values (?,?,?)', (url, flv[0], flv[1]))
        self._conn.commit()
        c.close()
        return urls

    def run(self):
        print 'Searching...'
        entries = YoutubeSearch(self.keyword)
        print 'Found', len(entries)
        for entry in entries:
            if self.quit:
                return
            # we absolutly want a thumbnail
            if len(entry['thumbnail']) == 0:
                continue
            # download the true url
            print 'Search', entry['url']
            urls = self._get_flventries(entry['url'])
            if urls is None:
                continue
            format, url = urls[0]

            # select the bigger
            w = 0
            select = None
            for thumb in entry['thumbnail']:
                if int(thumb['width']) > w:
                    select = thumb
                    w = int(thumb['width'])
            # download
            local_path = self._download_thumbnail(select['url'])
            # append to queue
            self.queue.append((url, entry['title'], local_path))

            #time.sleep(.10)

        print 'Done !'


class MTYoutubeVideo(MTScatterImage):
    def __init__(self, **kwargs):
        super(MTYoutubeVideo, self).__init__(**kwargs)
        self.urlvideo = kwargs.get('urlvideo')
        self.title = kwargs.get('title')
        self.video = None
        self.dt = 0

    def stop(self):
        if self.video:
            self.video.player.stop()
            self.video.player.unload()
            del self.video

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            if not self.video:
                self.video = MTSimpleVideo(filename=self.urlvideo)
                self.add_widget(self.video)
                self.video.player.play()
            else:
                if self.video.player.state == 'playing':
                    self.video.player.stop()
                else:
                    self.video.player.play()
            return True
        return super(MTYoutubeVideo, self).on_touch_down(touch)

    def draw(self):
        set_color(65/255., 123/255., 161/255., .6)
        drawRectangle(pos=(-10, -30), size=(self.width + 20, self.height + 40))
        super(MTYoutubeVideo, self).draw()
        if self.video:
            if self.video.size != (0, 0):
                self.size = self.video.size
            else:
                # draw progress loading circle
                self.dt += getFrameDt() * 300
                set_color(1, 1, 1, .7)
                drawSemiCircle(pos=Vector(self.size) / 2., start_angle=self.dt %
                               360, sweep_angle=275,
                               inner_radius=50, outer_radius=80)
        drawLabel(self.title, center=False, font_size=15, pos=(0, -5),
                  anchor_y='top', size=self.size)


class MTYoutubeSearchBox(MTBoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('padding', 50)
        kwargs.setdefault('margin', 50)
        super(MTYoutubeSearchBox, self).__init__(**kwargs)
        self.x = -2000
        self.go = MTButton(label='Search >', font_size=50, size=(350, 100),
                           style={'bg-color': (65/255., 123/255., 161/255., .6)}, halign='center')
        self.add_widget(self.go)
        self.textinput = MTTextInput(font_size=50)
        self.add_widget(self.textinput)
        self._init_ = False

        self.register_event_type('on_search')
        self.textinput.connect('on_text_validate', self.validate)
        self.go.connect('on_press', self.validate)

    def on_search(self, value):
        pass

    def validate(self, *largs):
        value = self.textinput.label
        if value == '':
            return
        self.textinput.hide_keyboard()
        self.hide()
        self.dispatch_event('on_search', value)

    def draw(self):
        if self._init_ == False:
            self.show()
            self._init_ = True

        w = self.get_parent_window()
        if w:
            self.y = w.height / 2. - self.height / 2.
            self.do_layout()
            self.width = w.width

        set_color(.1, .1, .1, .8)
        drawRectangle(pos=self.pos, size=self.size)

    def hide(self):
        self.do(Animation(duration=1.5, x=-2000, alpha_function='ease_out_cubic'))

    def show(self):
        self.do(Animation(duration=.5, x=0, alpha_function='ease_out_cubic'))


class MTYoutubeBrowser(MTWidget):
    def __init__(self, keyword, **kwargs):
        super(MTYoutubeBrowser, self).__init__(**kwargs)
        self.searcher = None
        self.searchbox = MTYoutubeSearchBox()
        self.searchbox.connect('on_search', self.on_search)
        self.add_widget(self.searchbox)
        self.hidesearch = MTButton(label='Restart',
                           style={'bg-color': (65/255., 123/255., 161/255., .2)}, halign='center')
        self.add_widget(self.hidesearch)
        self.hidesearch.hide()
        self.hidesearch.connect('on_release', self.restart)

    def _delete_child(self, child, *largs):
        if child in self.children:
            child.stop()
            self.children.remove(child)

    def restart(self, *largs):
        for child in self.children.iterate():
            if child.__class__ == MTYoutubeVideo:
                child.push_handlers(on_animation_complete=curry(self._delete_child, child))
                a = Animation(duration=.5, scale=0.001)
                child.do(a)
        self.searcher = None
        self.searchbox.show()
        self.hidesearch.hide()

    def on_search(self, value):
        self.searcher = YoutubeSearcher(value)
        self.searcher.start()
        self.hidesearch.show()

    def on_update(self):
        w = self.get_parent_window()
        self.hidesearch.pos = w.width / 2. - 50, w.height / 2. - 50
        super(MTYoutubeBrowser, self).on_update()
        if not self.searcher:
            return
        while True:
            try:
                e = self.searcher.queue.pop()
            except IndexError:
                return

            url, title, localname = e
            w = self.get_parent_window()

            # generate a position comming everywhere on the plane
            d = random.random() * 20
            dx = math.cos(d) * w.width
            dy = math.sin(d) * w.height
            x = w.width / 2. + dx * 0.25
            y = w.height / 2. + dy * 0.25
            sx = w.width / 2. + dx * 2
            sy = w.height / 2. + dy * 2
            wid = MTYoutubeVideo(title=title,
                urlvideo=url, filename=str(localname),
                size=(320, 240), pos=(sx, sy),
                rotation=(d*360.) % 360)
            wid.do(Animation(duration=1.5, pos=(x, y), alpha_function='ease_in_out_back'))
            self.add_widget(wid)

    def on_touch_down(self, touch):
        if super(MTYoutubeBrowser, self).on_touch_down(touch):
            return True
        if not touch.is_double_tap:
            return False
        self.arrange_circle()
        return True

    def arrange_circle(self):
        count = len(self.children) - 2
        if count == 0:
            return
        w = self.get_parent_window()
        d = (2 * math.pi) / float(count)
        j = 0
        for i in xrange(count):
            dx = w.width / 2.
            dy = w.height / 2.
            dx += math.cos(d * i) * (w.width / 4.)
            dy += math.sin(d * i) * (w.height / 4.)
            rotation = (d * i) / (2 * math.pi) * 360. + 90
            while self.children[j].__class__ != MTYoutubeVideo:
                j += 1
            self.children[j].do(Animation(
                duration=1.5, pos=(dx, dy), rotation=rotation, scale=1,
                alpha_function='ease_out_bounce'))
            j += 1

class Background(MTWidget):
    def __init__(self):
        super(Background, self).__init__()
        self.background = Image('background.jpg')

    def draw(self):
        w = getWindow()
        w.gradient = False
        set_color(1, 1, 1)
        drawTexturedRectangle(self.background.texture, size=w.size)

        h2 = w.height / 2.
        l = []
        l2 = []
        t = getClock().get_time()
        for x in xrange(0, w.width + 50, 50):
            l.append(x)
            l.append(h2 - 120 + math.sin(x * 0.01 + t * 0.3) * 30)
            l.append(x)
            l.append(h2 + 120 + math.sin(0.01 + x * 0.01 + t * 0.15) * 30)
            l2.append(x)
            l2.append(h2 - 200 + math.cos(x * 0.01 - t * 0.2) * 30)
            l2.append(x)
            l2.append(h2 + 140 + math.cos(0.01 + x * 0.01 - t * 0.3) * 30)
        set_color(65 / 255., 123 / 255., 161 / 255., .2)
        drawPolygon(l, style=GL_TRIANGLE_STRIP)
        drawPolygon(l2, style=GL_TRIANGLE_STRIP)


if __name__ == '__main__':
    w = getWindow()

    background = Background()
    w.add_widget(background)

    browser = MTYoutubeBrowser('multitouch')
    w.add_widget(browser)

    runTouchApp()
