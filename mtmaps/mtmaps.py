'''
Map browser, based on Modest Maps and PyMT
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

import os

current_directory = os.path.abspath(os.path.dirname(__file__))

#--------------------------------------------------------------------
# Config part
#--------------------------------------------------------------------

# Pickle caching prevent to convert image from jpg/png to rgba
# representation. This will cost you more space disk, and can
# introduce lag for tiny configuration.
# If you think that loading is too slow, try to enable this cache.
#
# Default to False.
#
map_config_enable_pickle = False

# Number of worker threads to download
#
# Default to 8
#
map_config_worker_threadss = 16

# Cache directory with all the maps in.
#
# Default to ./cache
map_config_cache_dir = os.path.join(current_directory, 'cache')





#--------------------------------------------------------------------
# Main part
#--------------------------------------------------------------------

import ModestMaps
import os, math, threading, time
if map_config_enable_pickle:
    import pickle
from pymt import *
from OpenGL.GL import *
from copy import copy
from Queue import Queue

ModestMaps.dataCacheDir = map_config_cache_dir

map_loader_stop = False
map_lock = threading.Lock()
map_queue_in = Queue()
map_queue_wait = []
map_queue_proc = {}
map_queue_out = {}

map_loader_inst = []

# register some cache
Cache.register('mtmaps.imagedata', limit=100)
Cache.register('mtmaps.texture', limit=100)

def map_filename(x1, y1, zoom, texx, texy, provider):
    filename = '%s.map' % ('='.join(map(lambda x: str(x), (x1, y1, zoom, texx, texy, provider))))
    return filename

def map_loader():
    while not map_loader_stop:
        filename = map_queue_in.get()
        if map_lock.acquire():
            map_queue_proc[filename] = True
            del map_queue_wait[map_queue_wait.index(filename)]
            map_lock.release()

        # get texture
        x1, y1, zoom, texx, texy, provider = filename.rsplit('.', 1)[0].split('=')
        x1, y1, zoom = map(float, (x1, y1, zoom))
        texx, texy = map(int, (texx, texy))
        provider = ModestMaps.builtinProviders[provider]()
        dim = ModestMaps.Core.Point(texx, texy)
        coord = ModestMaps.Core.Coordinate(x1, y1, zoom)
        mapCoord, mapOffset = ModestMaps.calculateMapCenter(provider, coord)
        mmap = ModestMaps.Map(provider, dim, mapCoord, mapOffset)
        image = mmap.draw(nocenter=True)

        # convert to gl texture (from pyglet)
        if image.mode not in ('RGB', 'RGBA'):
            raise Exception('Unsupported mode "%s"' % image.mode)

        if map_lock.acquire():
            map_queue_out[filename] = image
            try:
                del map_queue_proc[filename]
            except:
                pass
            map_lock.release()
        else:
            print 'FAILED'

def map_load(filename):
    map_config_enable_pickle = False

    data = Cache.get('mtmaps.imagedata', filename)
    if data:
        return data

    # load from cache if exist
    cache = os.path.join('cache', filename)
    if not map_config_enable_pickle or not os.path.exists(cache):

        if map_lock.acquire():
            if filename in map_queue_out:
                # file downloaded
                image = map_queue_out[filename]
                del map_queue_out[filename]
                map_lock.release()
            elif filename in map_queue_wait or filename in map_queue_proc:
                # map not yet loaded
                map_lock.release()
                return None
            else:
                # add map to download
                start_map_loader()
                map_queue_in.put(filename)
                map_queue_wait.append(filename)
                map_lock.release()
                return None

        width, height = image.size
        mode = image.mode
        data = image.tostring()

        # cache
        if map_config_enable_pickle:
            fd = open(cache, 'wb')
            pickle.dump([width, height, mode, data], fd)
            fd.close()

    else:
        print 'load from cache:', filename
        fd = open(cache, 'rb')
        width, height, mode, data = pickle.load(fd)
        fd.close()

    data = ImageData(width, height, mode, data)
    Cache.append('mtmaps.imagedata', filename, data)
    return data

class InteractiveMapTips(MTSpeechBubble):
    def __init__(self, **kwargs):
        kwargs.setdefault('size', (120, 100))
        kwargs.setdefault('font_size', 10)
        kwargs.setdefault('bold', True)
        kwargs.setdefault('bordercolor', (1,1,1,0.8))
        kwargs.setdefault('bordersize', 0)
        kwargs.setdefault('bgcolor', (0,0,0,.8))
        kwargs.setdefault('trisize', 15)
        kwargs.setdefault('map', None)
        super(InteractiveMapTips, self).__init__(**kwargs)
        self.map = kwargs.get('map')
        self.update()

    def update(self):
        if not self.map:
            return
        x, y = self.map.position_to_location(self.x, self.y)
        self.label = "X: %.4f\nY: %.4f\nLat: %.4f\nLon: %.4f" % (self.x, self.y, x, y)

class ScatterMap(MTScatterPlane):
    def __init__(self, **kwargs):
        super(ScatterMap, self).__init__(**kwargs)
        self.minscale = 1
        self.maxscale = 256

    def apply_angle_scale_trans(self, angle, scale, trans, point):
        newscale = self.scale * scale
        if newscale < self.minscale or newscale > self.maxscale:
            newscale = 1
        super(ScatterMap, self).apply_angle_scale_trans(angle, scale, trans, point)


class InteractiveMap(ScatterMap):
    def __init__(self, **kwargs):
        kwargs.setdefault('provider', 'BLUE_MARBLE')
        kwargs.setdefault('do_rotation', False)
        kwargs.setdefault('show_border', False)
        super(InteractiveMap, self).__init__(**kwargs)

        self.show_border = kwargs.get('show_border')
        self.touch_infos = {}

        # start with zoom 1 - 25
        self.oldzoom = self.zoom = 1
        self.maxzoomlevel = 35

        # set maxzoomlevel on scale
        self.maxscale = math.pow(2, self.maxzoomlevel)

        # stats
        self.tilecount = 0

        # init provider
        self.provider_ids_btns = {}
        providers = {
            'OPENSTREETMAP': 'OpenStreetMap',
            'BLUE_MARBLE': 'Blue Marble',
            'MICROSOFT_ROAD': 'Microsoft Road',
            'MICROSOFT_AERIAL': 'Microsoft Aerial',
            'MICROSOFT_HYBRID': 'Microsoft Hybrid',
            #'YAHOO_ROAD': 'Yahoo Road',
            #'YAHOO_AERIAL': 'Yahoo Aerial',
            #'YAHOO_HYBRID': 'Yahoo Hybrid',
        }

        # ui provider
        self.ui = MTBoxLayout(pos=(20, 20), uniform_width=True,
                             orientation='vertical', spacing=1, padding=10)
        k = { 'bold': True, 'size': (150, 30), 'color_down': (.7,.7,.7,.6),
             'halign': 'center' }
        for provider in providers:
            button = MTToggleButton(label=providers[provider], **k)
            button.push_handlers(on_press=curry(self.on_press_provider, provider))
            self.ui.add_widget(button)
            self.provider_ids_btns[provider] = button

        # init interface
        self.btn_border = MTToggleButton(label='Borders', **k)
        self.btn_border.push_handlers(on_press=self.on_press_border)
        self.ui.add_widget(MTWidget(size=(150, 10)))
        self.ui.add_widget(self.btn_border)
        self.ui.add_widget(MTWidget(size=(150, 10)))

        k['size'] = (150, 20)
        k['halign'] = 'left'
        kr = copy(k)
        kr['halign'] = 'right'
        kr['bold'] = False
        kr['size'] = (150, 15)
        self.lbl_position = MTLabel(label='-', **kr)
        self.ui.add_widget(self.lbl_position)
        self.ui.add_widget(MTLabel(label='Position', **k))

        self.lbl_zoomlevel = MTLabel(label='-', **kr)
        self.ui.add_widget(self.lbl_zoomlevel)
        self.ui.add_widget(MTLabel(label='Zoom level', **k))

        self.lbl_tilesqueue = MTLabel(label='-', **kr)
        self.ui.add_widget(self.lbl_tilesqueue)
        self.ui.add_widget(MTLabel(label='Queue in/proc/out', **k))

        self.lbl_tilescached = MTLabel(label='-', **kr)
        self.ui.add_widget(self.lbl_tilescached)
        self.ui.add_widget(MTLabel(label='Tiles cached', **k))

        self.lbl_tilesdisplayed = MTLabel(label='-', **kr)
        self.ui.add_widget(self.lbl_tilesdisplayed)
        self.ui.add_widget(MTLabel(label='Tiles displayed', **k))

        # now, set default provider
        self.set_provider(kwargs.get('provider'))


    def on_press_provider(self, provider, *largs):
        self.set_provider(provider)

    def set_provider(self, provider):
        self.provider_id = provider
        self.provider = ModestMaps.builtinProviders[self.provider_id]()
        self.texsize = (self.provider.tileWidth(), self.provider.tileHeight())
        for p in self.provider_ids_btns:
            self.provider_ids_btns[p].set_state('normal')
        self.provider_ids_btns[provider].set_state('down')

    def position_to_location(self, x, y):
        pzoom = math.pow(2, self.zoom - 1)
        bound = int(math.pow(2, self.zoom))
        x, y = map(lambda x: float(x) * pzoom, self.to_local(x, y))
        x, y = map(lambda x: x / float(self.texsize[0]), (x, y))
        x, y = map(lambda x: x % bound, (x, y))
        coord = ModestMaps.Core.Coordinate(x, y, self.zoom)
        loc = self.provider.coordinateLocation(coord)
        return loc.lon, loc.lat

    def on_press_border(self, *largs):
        self.show_border = not self.show_border

    def on_touch_down(self, touch):
        if self.ui.dispatch_event('on_touch_down', touch):
            return True
        self.touch_infos[touch.id] = InteractiveMapTips(pos=(touch.x, touch.y), map=self)
        return super(InteractiveMap, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.id in self.touch_infos:
            self.touch_infos[touch.id].pos = touch.x, touch.y
            self.touch_infos[touch.id].update()
        if self.ui.dispatch_event('on_touch_move', touch):
            return True
        return super(InteractiveMap, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.id in self.touch_infos:
            del self.touch_infos[touch.id]
        if self.ui.dispatch_event('on_touch_up', touch):
            return True
        return super(InteractiveMap, self).on_touch_up(touch)

    def on_draw(self):
        super(InteractiveMap, self).on_draw()
        self.draw_static()
        self.draw_touches()

    def draw_touches(self):
        for n in reversed(self.touch_infos.keys()):
            self.touch_infos[n].draw()

    def draw_static(self):
        '''Draw static interface (ie: not in scatter)'''
        if map_lock.acquire():
            lin = len(map_queue_wait)
            lout = len(map_queue_out)
            lproc = len(map_queue_proc)
            map_lock.release()

        self.lbl_position.label = '%.2f %.2f' % (self.pos[0], self.pos[1])
        self.lbl_zoomlevel.label = '%d' % (self.zoom)
        self.lbl_tilesqueue.label = '%d/%d/%d' % (lin, lproc, lout)
        self.lbl_tilesdisplayed.label = '%d' % (self.tilecount)
        self.lbl_tilescached.label = '%d' % (len(Cache._objects['mtmaps.imagedata']))

        set_color(0, 0, 0, 0.8)
        drawRoundedRectangle(pos=self.ui.pos, size=self.ui.size)
        self.ui.dispatch_event('on_draw')

    def draw(self):
        # reset stats
        self.tilecount = 0

        # get zoom from scale
        zoom = int(self.scale)
        if zoom <= 0:
            zoom = 1

        # cache pow2 table
        if not hasattr(self, 'pow2'):
            self.pow2 = map(lambda x: math.pow(2, x), range(0, self.maxzoomlevel))

        # search the nearet power of 2
        while True:
            if zoom in self.pow2:
                zoom = self.pow2.index(zoom)
                break
            zoom -= 1

        # increment zoom for nicer image
        zoom += 1
        if zoom < 1:
            zoom = 1
        self.zoom = zoom

        # reset cache when zooming ?
        if self.oldzoom != self.zoom:
            self.oldzoom = self.zoom
            if map_lock.acquire():
                try:
                    while True:
                        map_queue_in.get(False)
                except:
                    pass
                map_lock.release()

        # calculate boundaries
        w = self.get_parent_window()
        self.omin = self.to_local(0, 0)
        self.omax = self.to_local(w.size[0], w.size[1])

        # if we got a upper zoom, draw it before down zoom
        for z in range(1, self.zoom + 1):
            self.draw_for_zoom(z)

    def draw_for_zoom(self, zoom):
        # initialize
        dt = getFrameDt()
        origin = ModestMaps.Core.Coordinate(0, 1, 1)
        pzoom = math.pow(2, zoom - 1)
        bound = int(math.pow(2, zoom))
        maxtex = 1

        # clamp to texsize
        minx, miny = self.omin[0] / self.texsize[0], self.omin[1] / self.texsize[1]
        maxx, maxy = self.omax[0] / self.texsize[0], self.omax[1] / self.texsize[1]
        minx, maxx, miny, maxy = map(lambda x: int(x * pzoom), (minx, maxx, miny, maxy))
        minx -= 1
        maxx += 1
        miny -= 1
        maxy += 1

        # draw !
        tilecount = 0
        for x in xrange(minx, maxx):
            for y in xrange(miny, maxy):
                # stats
                tilecount += 1

                # texture coord
                tx, ty = x * self.texsize[0] / pzoom, y * self.texsize[1] / pzoom

                # get coordinate for x/y
                nx = x % int(bound)
                ny = y % int(bound)
                c = origin.copy()
                c = c.right(nx).down(bound-ny)

                # load ?
                id = map_filename(c.row, c.column, zoom, self.texsize[0], self.texsize[1], self.provider_id)

                tex = Cache.get('mtmaps.texture', id)
                if tex is None:
                    data = map_load(id)
                    if data:
                        tex = Texture.create_from_data(data)
                        tex.flip_vertical()
                        Cache.append('mtmaps.texture', id, tex)
                if tex:
                    tex_ts = Cache.get_timestamp('mtmaps.texture', id)
                    #data._alpha += dt * 2
                    alpha = boundary(2 * (getClock().get_time() - tex_ts), 0, 1)
                    set_color(1,1,1,alpha)
                    drawTexturedRectangle(pos=(tx, ty),
                                          size=(self.texsize[0]/pzoom, self.texsize[1]/pzoom),
                                          texture=tex)
                '''
                if data:
                    do_draw = True
                    if not hasattr(data, '_current_texture'):
                        if maxtex > 0:
                            # first time, set clamp
                            texture = Texture.create_from_data(data)
                            #data._alpha = 0
                            #glTexParameteri(tex.target, GL_TEXTURE_WRAP_S, GL_CLAMP)
                            #glTexParameteri(tex.target, GL_TEXTURE_WRAP_T, GL_CLAMP)
                            data._current_texture = texture

                            maxtex -= 1
                        else:
                            do_draw = False
                    else:
                        tex = data._current_texture
                        data._alpha += dt * 2

                    # draw texture
                    if do_draw:
                        set_color(1,1,1,data._alpha)
                        drawTexturedRectangle(pos=(tx, ty), size=(self.texsize[0]/pzoom,
                                              self.texsize[1]/pzoom), texture=tex)

                else:
                    pass
                '''

                # draw borders
                if self.show_border:
                    set_color(1,1,1,0.8)
                    drawRectangle(pos=(tx,ty), size=(self.texsize[0]/pzoom,
                                             self.texsize[1]/pzoom), style=GL_LINE_LOOP)

        # update stats
        self.tilecount += tilecount



def start_map_loader():
    global map_loader_inst, map_config_worker_threadss
    if len(map_loader_inst) > 0:
        return
    for i in range(0, map_config_worker_threadss):
        m = threading.Thread(target=map_loader)
        m.daemon = True
        m.start()
        map_loader_inst.append(m)


def start():
    imap = InteractiveMap()
    return imap

def stop(wid):
    global map_loader_inst
    map_loader_stop = True
    del map_loader_inst
    del wid

if __name__ == '__main__':
    from pymt import *

    w = MTWindow()
    wid = start()
    w.add_widget(wid)
    runTouchApp()
    stop(wid)
    w.remove_widget(wid)
