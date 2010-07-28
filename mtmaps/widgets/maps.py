'''
Note: Future widget for PyMT, development in progress.
'''

__all__ = ('MapViewer', 'TileServer', )

from math import pi, sin, cos, atan2, sqrt, radians, log, atan, exp, tan
from os.path import join, dirname, exists, sep
from os import makedirs, mkdir
from threading import Condition, Thread
from collections import deque
from httplib import HTTPConnection
from random import randint

from pymt import *
from OpenGL.GL import GL_LINE_LOOP, GL_CLAMP

#
# Module configuration
#

# Google Maps specific
GMAPS_CROPSIZE = 30

# Map Plane configuration

# zoom to start to
MAP_ZOOM0 = 0

# number of threads to use
TILESERVER_POOLSIZE = 20
TILESERVER_MAXPIPELINE = 3

# size of tiles
TILE_W = 256
TILE_H = 256

# register a cache for tiles
Cache.register('tileserver.tiles', limit=500, timeout=10)
Cache.register('tileserver.tilesalpha', limit=500, timeout=10)

#
# Projection functions
#
# http://code.google.com/p/googleio2009-map/source/browse/trunk/tiles/gmaps-tiler.py
#
def fix180(x):
    return ((x + 180) % 360) - 180

def project(lat, lon):
  '''Projects the given lat/lon to bent mercator image
     coordinates [-1,1] x [-1,1].
  '''
  return (lon / 180.0, log(
      tan(pi / 4 + (lat * pi / 180.0) / 2)) / pi)


def unproject(x, y):
  '''Unprojects the given bent mercator image coordinates [-1,1] x [-1,1] to
     the lat/lon space.
  '''
  return ((2 * atan(exp(y * pi)) - pi / 2)
      * 180.0 / pi, x * 180)


#
# Tiles parts
#

class TileServer(object):
    '''Base implementation for a tile provider.
    Check GoogleTileServer and YahooTileServer if you intend to use more
    '''
    provider_name = 'unknown'
    providers = dict()

    @staticmethod
    def register(cls):
        TileServer.providers[cls.provider_name] = cls

    def __init__(self, poolsize=TILESERVER_POOLSIZE):
        self.cache_path = join(dirname(__file__), 'cache', self.provider_name)
        if not exists(self.cache_path):
            makedirs(self.cache_path)

        self.q_in       = deque()
        self.q_out      = deque()
        self.q_count    = 0
        self.c_in       = Condition()
        self.workers    = []
        self.poolsize   = poolsize
        self.uniqid     = 1
        self.want_close = False
        self.available_maptype = dict(roadmap='Roadmap')

    def start(self):
        '''Start all the workers
        '''
        for i in xrange(self.poolsize):
            self.create_worker()

    def create_worker(self):
        '''Create a new worker, and append to the list of current workers
        '''
        thread = Thread(target=self._worker_run,
                        args=(self.c_in, self.q_in, self.q_out))
        thread.daemon = True
        thread.start()
        self.workers.append(thread)

    def stop(self, wait=False):
        '''Stop all workers
        '''
        self.want_close = True
        if wait:
            for x in self.workers:
                x.join()


    def post_download(self, filename):
        '''Callback called after the download append. You can use it for
        doing some image processing, like cropping

        .. warning::
            This function is called inside a worker Thread.
        '''
        pass

    def to_filename(self, nx, ny, zoom, maptype, format):
        fid = self.to_id(nx, ny, zoom, maptype, format)
        hash = fid[0:2]
        return join(self.cache_path, hash, fid)

    def to_id(self, nx, ny, zoom, maptype, format):
        return '%d_%d_%d_%s.%s' % (nx, ny, zoom, maptype, format)

    def exist(self, nx, ny, zoom, maptype, format='png'):
        filename = self.to_filename(nx, ny, zoom, maptype, format)
        img = Cache.get('tileserver.tiles', filename)
        return bool(img)

    def get(self, nx, ny, zoom, maptype, format='png'):
        '''Get a tile
        '''
        filename = self.to_filename(nx, ny, zoom, maptype, format)
        img = Cache.get('tileserver.tiles', filename)

        # check if the tile is already beeing loaded
        if img is False:
            return None

        # check if the tile exist in the cache
        if img is not None:
            return img

        # no tile, ask to workers to download 
        Cache.append('tileserver.tiles', filename, False)
        self.q_count += 1
        self.q_in.append((nx, ny, zoom, maptype, format))
        self.c_in.acquire()
        self.c_in.notify()
        self.c_in.release()
        return None

    def update(self):
        '''Must be called to get pull image from the workers queue
        '''
        pop = self.q_out.pop
        while True:
            try:
                filename, image = pop()
                self.q_count -= 1
            except:
                return
            Cache.append('tileserver.tiles', filename, image)

    def _worker_run(self, c_in, q_in, q_out):
        '''Internal. Main function for every worker
        '''
        conn = HTTPConnection(self.provider_host)
        do = self._worker_run_once

        while not self.want_close:
            try:
                do(conn, c_in, q_in, q_out)
            except:
                pymt_logger.exception('TileServerWorker: Unknown exception, stop the worker')
                return

    def _worker_run_once(self, conn, c_in, q_in, q_out):
        '''Internal. Load one image, process, and push.
        '''
        # get one tile to process
        try:
            nx, ny, zoom, maptype, format = q_in.pop()
        except:
            c_in.acquire()
            c_in.wait()
            c_in.release()
            return

        # check if the tile already have been downloaded
        filename = self.to_filename(nx, ny, zoom, maptype, format)
        if not exists(filename):

            # calculate the good tile index
            tz = pow(2, zoom)
            lx, ly = unproject(2.0 * (nx + 0.5) / tz - 1, 1 - 2.0 * (ny + 0.5) / tz)
            lx, ly = map(fix180, (lx, ly))

            # get url for this specific tile
            url = self.geturl(
                nx=nx, ny=ny,
                lx=lx, ly=ly,
                tilew=256, tileh=256,
                zoom=zoom,
                format=format,
                maptype=maptype
            )

            # load url content
            try:
                conn.request('GET', url)
                res = conn.getresponse()
                data = res.read()
                if res.status < 200 or res.status >= 300:
                    raise Exception('Invalid HTTP Code %d:%s' % (
                        res.status, res.reason))
            except Exception, e:
                pymt_logger.error('TileServer: %s: %s' % (str(e), filename))
                pymt_logger.error('TileServer: URL=%s' % url)
                return

            # write data on disk
            try:
                directory = sep.join(filename.split(sep)[:-1])
                if not exists(directory):
                    mkdir(directory)
                with open(filename, 'wb') as fd:
                    fd.write(data)
            except:
                pymt_logger.exception('Tileserver: Unable to write %s' % filename)
                return

            # post processing
            self.post_download(filename)

        # load image
        image = ImageLoader.load(filename)
        image.id = 'img%d' % self.uniqid
        self.uniqid += 1

        # push image on the queue
        q_out.appendleft((filename, image))



class GoogleTileServer(TileServer):
    '''Google tile server.

    .. warning::
        This tile server will not work, cause of limitation of Google.
        It's just for testing purpose, don't use it !
    '''

    provider_name = 'google'
    provider_host = 'maps.google.com'
    available_maptype = dict(roadmap='Roadmap')

    def geturl(self, **infos):
        infos['tileh'] += GMAPS_CROPSIZE * 2 # for cropping
        return '/maps/api/staticmap?center=' + \
               "%(lx)f,%(ly)f&zoom=%(zoom)d&size=%(tilew)dx%(tileh)d" \
               "&sensor=false&maptype=%(maptype)s&format=%(format)s" % \
               infos

    def post_download(self, filename):
        # Reread the file with pygame to crop it
        import pygame
        img = pygame.image.load(filename)
        img = img.subsurface((0, GMAPS_CROPSIZE, 256, 256))
        pygame.image.save(img, filename)

class YahooTileServer(TileServer):
    '''Yahoo tile server implementation
    '''

    provider_name = 'yahoo'
    provider_host = 'us.maps2.yimg.com'
    available_maptype = dict(roadmap='Roadmap')

    def geturl(self, **infos):
        def toYahoo(col, row, zoom):
            x = col
            y = int(pow(2, zoom - 1) - row - 1)
            z = 18 - zoom
            return x, y, z
        coordinates = 'x=%d&y=%d&z=%d' % toYahoo(infos['nx'], infos['ny'], infos['zoom'])
        return '/us.png.maps.yimg.com/png?v=%s&t=m&%s' % \
            ('3.52', coordinates)

class BlueMarbleTileServer(TileServer):
    '''Blue Marble tile server implementation
    '''

    provider_name = 'bluemarble'
    provider_host = 's3.amazonaws.com'
    available_maptype = dict(roadmap='Satellite')
    def geturl(self, **infos):
        return '/com.modestmaps.bluemarble/%d-r%d-c%d.jpg' % (
            infos['zoom'], infos['ny'], infos['nx']
        )

class BingTileServer(TileServer):
    '''Bing tile server implementation. Support road and satellite
    '''

    provider_name = 'bing'
    available_maptype = dict(roadmap='Roadmap', satellite='Satellite')

    def geturl(self, **infos):
        octalStrings = ('000', '001', '010', '011', '100', '101', '110', '111')
        microsoftToCorners = {'00': '0', '01': '1', '10': '2', '11': '3'}
        def toBinaryString(i):
            return ''.join([octalStrings[int(c)] for c in oct(i)]).lstrip('0')
        def toMicrosoft(col, row, zoom):
            x = col
            y = row
            y, x = toBinaryString(y).rjust(zoom, '0'), toBinaryString(x).rjust(zoom, '0')
            string = ''.join([microsoftToCorners[y[c]+x[c]] for c in range(zoom)])
            return string
        if infos['maptype'] in ('satellite', 'aerial'):
            mapprefix = 'h'
        else:
            mapprefix = 'r'
        return '/tiles/%s%s.png?g=90&shading=hill' % \
            (mapprefix, toMicrosoft(infos['nx'], infos['ny'], infos['zoom']))

    @property
    def provider_host(self):
        return 'r%d.ortho.tiles.virtualearth.net' % randint(0, 3)

class OpenStreetMapTileServer(TileServer):
    '''OSM tile server implementation
    '''

    provider_name = 'openstreetmap'
    provider_host = 'tile.openstreetmap.org'
    available_maptype = dict(roadmap='Roadmap')

    def geturl(self, **infos):
        row, col, zoom = infos['nx'], infos['ny'], infos['zoom']
        return '/%d/%d/%d.png' % (zoom, row, col)


#
# Registers
#
TileServer.register(BlueMarbleTileServer)
TileServer.register(BingTileServer)
TileServer.register(YahooTileServer)
TileServer.register(OpenStreetMapTileServer)
#TileServer.register(GoogleTileServer)


class MapViewerPlane(MTScatterPlane):
    '''Infinite plane, cropped to the screen size, and display only tiles on the
    screen.

    :Parameters:
        `provider`: str, default to 'bing'
            Provider to use
        `tileserver`: TileServer, default to None
            Specify a custom tileserver class to use
    '''
    def __init__(self, **kwargs):
        kwargs.setdefault('do_rotation', False)
        kwargs.setdefault('show_border', False)
        kwargs.setdefault('scale_min', 1)
        super(MapViewerPlane, self).__init__(**kwargs)
        self.minscale = MAP_ZOOM0
        self.maxscale = 256

        self.show_border = kwargs.get('show_border')
        self.maptype = kwargs.get('maptype', 'satellite')

        self._tileserver = None
        self.tileserver = kwargs.get('tileserver', None)
        if self.tileserver is None:
            self.provider = kwargs.get('provider', 'bing')

        # start with zoom 1 - 25
        self.maxzoomlevel = 35
        self.quality = 1
        self.xy = 0, 0
        self.tilecount = 0

        # set maxzoomlevel on scale
        self.maxscale = pow(2, self.maxzoomlevel)

        self._cache_bbox = None
        self.tiles = []

    def _get_provider(self):
        if self._tileserver:
            return self._tileserver.provider_name
        return ''
    def _set_provider(self, x):
        if x == self.provider:
            return
        if x in TileServer.providers:
            self.tileserver = TileServer.providers[x]()
        else:
            raise Exception('Unknown map provider %s' % x)
    provider = property(_get_provider, _set_provider)

    def _get_tileserver(self):
        return self._tileserver
    def _set_tileserver(self, x):
        if x == self._tileserver:
            return
        if self._tileserver is not None:
            self._tileserver.stop()
        self._tileserver = x
        self._tileserver.start()
    tileserver = property(_get_tileserver, _set_tileserver)

    def get_latlon_from_xy(self, x, y, local=False):
        '''Get latitude/longitude from x/y in scatter (x/y will be transformed
        in scatter coordinate space)
        '''
        if local is False:
            x, y = self.to_local(x, y)
        p = Vector(x, y) / (TILE_W, TILE_H)
        nx = (p.x % 2) - 1
        ny = 1 - (p.y % 2)
        lx, ly = unproject(nx, (-ny))
        return lx, ly

    def get_xy_from_latlon(self, lat, lon):
        '''Return x/y location from latitude/longitude
        '''
        x, y = project(lat, lon)
        return Vector(x + 1, y + 1) * (TILE_W, TILE_H)


    def move_to(self, latlon, latlon2, **kwargs):
        '''Move the view to a rectangle of latlon to latlon2
        '''
        kwargs.setdefault('duration', 2)
        kwargs.setdefault('alpha_function', 'ease_in_out_quad')

        # Save, beacause well let scatter do actual computation
        # on its transform. Then reset it once we know the rigth
        # values, and thenuse animate ;P
        old_scale = self.scale
        old_center = self.center

        local_pos1 = Vector(self.get_xy_from_latlon(*latlon))
        local_pos2 = Vector(self.get_xy_from_latlon(*latlon2))

        # translate in parent space becasue apply_angle_scale_trans
        # takes parent space coords
        pos1 = Vector(self.to_parent(*local_pos1))
        pos2 = Vector(self.to_parent(*local_pos2))

        # middle between p1 and p2
        middle = (pos1 + 0.5*(pos2-pos1))

        # center of screen
        center = Vector(self.parent.center)

        # move by the amount parent center is away from middle
        # of wanted bounding box
        translate =  center - middle
        self.apply_angle_scale_trans(0, 1, translate, point=Vector(0,0))

        # scale factor is current width seen / width which we aim for
        # distance between p1, p2 in local space
        distance = max(local_pos1.distance(local_pos2), 0.0000001)
        # length of diagonal of screen
        screen_span = Vector(self.to_local(*self.parent.pos))
        screen_span = screen_span.distance(self.to_local(*center)) * 2
        scale = screen_span / distance - 0.1
        self.apply_angle_scale_trans(0, scale, Vector(0,0), point=center)

        if kwargs['duration'] == 0:
            return

        # self.center and scale are properties that are
        # computed dyanmically from scatter transform.
        # now that we know what tehy should be, we can easily animate :)
        anim1 = Animation(center=self.center, scale=self.scale, **kwargs)

        # restore current viewpoint and start animation
        self.center = old_center
        self.scale = old_scale
        self.do(anim1)

    def distance(self, latlon1, latlon2):
        '''Return distance between 2 latlon'''
        lat1, lon1 = map(radians, latlon1)
        lat2, lon2 = map(radians, latlon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2.0))**2
        c = 2 * atan2(sqrt(a), sqrt(1.0-a))
        km = 6371.0 * c
        return km

    @property
    def zoom(self):
        '''Get zoom from current scale'''
        self._zoom = max(1, int(log(self.scale, 2))) + self.quality
        return self._zoom

    def on_update(self):
        # update tileserver
        self.tileserver.update()
        super(MapViewerPlane, self).on_update()

    def apply_angle_scale_trans(self, angle, scale, trans, point):
        newscale = self.scale * scale
        if newscale < self.minscale or newscale > self.maxscale:
            newscale = 1
        super(MapViewerPlane, self).apply_angle_scale_trans(angle, scale, trans, point)

    def tile_bbox(self, zoom):
        pzoom = pow(2, zoom - MAP_ZOOM0)
        pzw = pzoom / float(TILE_W)
        pzh = pzoom / float(TILE_H)
        minx, miny = self.omin
        maxx, maxy = self.omax
        minx = int(minx * pzw)
        miny = int(miny * pzh)
        maxx = int(maxx * pzw)
        maxy = int(maxy * pzh)
        return (minx, miny, maxx, maxy)

    def draw(self):
        # calculate boundaries
        parent = self.parent
        if not parent:
            return
        self.omin = self.to_local(*parent.pos)
        self.omax = self.to_local(parent.x + parent.width, parent.y + parent.height)

        # draw background
        set_color(0, 0, 0)
        drawRectangle(pos=self.omin, size=Vector(self.omax) - self.omin)

        # check if we must invalidate the tiles
        bbox = self.tile_bbox(self.zoom)
        if self._cache_bbox != bbox:
            self._cache_bbox = bbox
            self.tiles = []

        if not self.tiles:
            # precalculate every tiles needed for each zoom
            # from the current zoom to the minimum zoom
            # if the current zoom is completly loaded,
            # drop the previous zoom
            self.tiles = tiles = []
            will_break = False
            for z in xrange(self.zoom, 0, -1):
                if self.compute_tiles_for_zoom(z, tiles):
                    if z > 0:
                        self.compute_tiles_for_zoom(z - 1, tiles)
                    break

        # now draw tiles
        for tile in reversed(self.tiles):
            self.tile_draw(*tile)

    def compute_tiles_for_zoom(self, zoom, tiles):
        '''Calculate and put on `tiles` all tiles needed to draw this zoom
        level.
        '''
        # initialize
        pzoom = pow(2, zoom - 1 - MAP_ZOOM0)
        bound = int(pow(2, zoom))
        tw = TILE_W / float(pzoom)
        th = TILE_H / float(pzoom)
        ret = True

        # clamp to texsize
        pzw = pzoom / float(TILE_W)
        pzh = pzoom / float(TILE_H)
        minx, miny = self.omin
        maxx, maxy = self.omax
        minx = int(minx * pzw)
        miny = int(miny * pzh)
        maxx = int(maxx * pzw)
        maxy = int(maxy * pzh)

        # Explaination about tile clamp
        #
        # if tilesize is 50
        # 0 ----------------------------- 100
        #           ^ value = 30
        # ^ clamped value = 0
        #                ^ value = 50
        #                ^ campled value = 50
        #                       ^ value = 65
        #                ^ campled value = 50
        # => value is clampled to the minimum
        #
        # So we have a trouble if the value is negative
        # -100 -------------------------- 0
        #                        ^ value = -30
        #                  ^ clamped value = -50
        #           ^ value = -75
        #  ^ clamped value = -100
        #
        # So we adjust clamp border for :
        # 1. take in account the clamp problem with negative value
        # 2. add one tile in every side to enhance user experience
        #    (load tile before it will be displayed)

        minx -= 1
        miny -= 1
        maxx += 1
        maxy += 1

        # draw !
        self.tilecount = 0
        for x in xrange(minx, maxx):
            for y in xrange(miny, maxy):
                # stats
                self.tilecount += 1

                # texture coord
                tx, ty = x * tw, y * th

                # get coordinate for x/y
                nx = x % int(bound)
                ny = y % int(bound)

                tile = (
                    nx, ny, tx, ty,
                    tw, th, zoom, bound
                )

                ret = ret and self.tile_exist(*tile)
                tiles.append(tile)

        return ret

    def tile_exist(self, nx, ny, tx, ty, sx, sy, zoom, bound):
        '''Check if a specific tile exist
        '''
        return self.tileserver.exist(nx, bound-ny-1, zoom, self.maptype)

    def tile_draw(self, nx, ny, tx, ty, sx, sy, zoom, bound):
        '''Draw a specific tile on the screen.
        Return False if the tile is not yet available.
        '''
        # nx, ny = index of tile
        # tx, ty = real position on scatter
        # sx, sy = real size on scatter
        # pzoom = current zoom level
        image = self.tileserver.get(nx, bound-ny-1, zoom, self.maptype)
        if image in (None, False):
            return

        if image.texture.wrap is None:
            image.texture.wrap = GL_CLAMP

        alpha = Cache.get('tileserver.tilesalpha', image.id)
        if alpha is None:
            alpha = 0
        alpha += getFrameDt() * 4
        Cache.append('tileserver.tilesalpha', image.id, alpha)

        set_color(1, 1, 1, alpha)
        drawTexturedRectangle(
            pos=(tx, ty), size=(sx, sy), texture=image.texture)

    def _get_state(self):
        parent = self.parent
        if not self.parent:
            return
        lat1, lon1 = self.get_latlon_from_xy(*parent.pos)
        lat2, lon2 = self.get_latlon_from_xy(parent.x + parent.width, parent.y + parent.height)
        return {
            'newark_lat': str(lat1),
            'locust_lat': str(lat2),
            'locust_lon': str(lon2),
            'newark_lon': str(lon1),
        }
    def _set_state(self, state, duration=0):
        newark_lon = float(state['newark_lon'])
        newark_lat = float(state['newark_lat'])
        locust_lon = float(state['locust_lon'])
        locust_lat = float(state['locust_lat'])
        locust = locust_lat, locust_lon
        newark = newark_lat, newark_lon
        self.move_to(newark, locust, duration=duration)
    state = property(_get_state, _set_state,
        doc='Get/Set the state of the widget (only viewport)')

class MapViewer(MTStencilContainer):
    '''Map viewer, bounded to a specific rectangle.
    '''
    def __init__(self, **kwargs):
        super(MapViewer, self).__init__(**kwargs)
        self.readonly = kwargs.get('readonly', False)
        if 'pos' in kwargs:
            del kwargs['pos']
        self.map = MapViewerPlane(**kwargs)
        self.add_widget(self.map)

    def world_diameter(self):
        left = self.map.get_latlon_from_xy(self.x, self.y)
        center = self.map.get_latlon_from_xy(*self.center)
        return 2 * self.map.distance(left, center)

    def on_update(self):
        self.map.size = self.size
        super(MapViewer, self).on_update()

    def on_touch_down(self, touch):
        if self.readonly:
            return
        if not self.collide_point(*touch.pos):
            return False
        return super(MapViewer, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.readonly:
            return
        if not self.collide_point(*touch.pos):
            return False
        return super(MapViewer, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.readonly:
            return
        if not self.collide_point(*touch.pos):
            return False
        return super(MapViewer, self).on_touch_up(touch)

MTWidgetFactory.register('MapViewer', MapViewer)

if __name__ == '__main__':

    sync_child = None
    sync_work = False
    def sync_maps(view, views, *l):
        global sync_work
        if sync_work:
            return
        if view is not sync_child:
            return
        sync_work = True
        for view in views:
            if view is sync_child:
                continue
            view.map.state = sync_child.map.state
        sync_work = False

    def sync_start(view, *l):
        global sync_child
        sync_child = view

    layout = MTBoxLayout()
    layout.add_widget(MapViewer(size_hint=(1, 1), provider='bing'))
    layout.add_widget(MapViewer(size_hint=(1, 1), provider='yahoo'))
    layout.add_widget(MapViewer(size_hint=(1, 1), provider='openstreetmap'))
    for children in layout.children:
        children.map.connect('on_touch_down', curry(sync_start, children))
        children.map.connect('on_transform', curry(sync_maps, children, layout.children))
    runTouchApp(layout)
