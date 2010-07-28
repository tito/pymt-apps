from pymt import *
from widgets.maps import MapViewer

css_add_sheet(
'''

mapsettings {
    bg-color: #000000;
}

.lbltitle {
    draw-background: 1;
    bg-color: #0992f3;
    font-weight: bold;
}

.lblsettingsk,
.lblsettingsv {
    font-size: 10;
    padding: 5 2;
}

.btnsettings {
    draw-border: 0;
    draw-alpha-background: 0;
}

''')

xml_settings = '''
<MTBoxLayout orientation='"vertical"' spacing='0'>
    <MTLabel cls='"lbltitle"' label='"Provider"' padding="5" size_hint='(1, None)'/>
    <MTToggleButton cls='"btnsettings"' size='(150, 30)' group='"mapbtn"' label='"Blue Marble"' id='"bluemarble"'/>
    <!--
    <MTToggleButton cls='"btnsettings"' size='(150, 30)' group='"mapbtn"' label='"Yahoo Roads"' id='"yahooroad"'/>
    -->
    <MTToggleButton cls='"btnsettings"' size='(150, 30)' group='"mapbtn"' label='"Bing Roads"' id='"bingroad"'/>
    <MTToggleButton cls='"btnsettings"' size='(150, 30)' group='"mapbtn"' label='"Bing Satellite"' id='"bingsatellite"'/>
    <MTToggleButton cls='"btnsettings"' size='(150, 30)' group='"mapbtn"' label='"OpenStreetMap"' id='"osm"'/>
    <MTLabel cls='"lbltitle"' label='"Informations"' padding="5" size_hint='(1, None)'/>
    <MTLabel cls='"lblsettingsk"' label='"Position"'/>
    <MTLabel cls='"lblsettingsv"' id='"lblpos"' label='"-"'/>
    <MTLabel cls='"lblsettingsk"' label='"Zoom level"'/>
    <MTLabel cls='"lblsettingsv"' id='"lblzoom"' label='"-"'/>
    <MTLabel cls='"lblsettingsk"' label='"Tiles displayed"'/>
    <MTLabel cls='"lblsettingsv"' id='"lbldisp"' label='"-"'/>
    <MTLabel cls='"lblsettingsk"' label='"Queue in/proc"'/>
    <MTLabel cls='"lblsettingsv"' id='"lblqueue"' label='"-"'/>
</MTBoxLayout>
'''

class MapSettings(MTSidePanel):
    def __init__(self, viewer, **kwargs):
        xml = XMLWidget(xml=xml_settings)
        corner = MTImageButton(filename='arrow.png')
        kwargs.setdefault('layout', xml.root)
        kwargs.setdefault('corner', corner)
        super(MapSettings, self).__init__(**kwargs)
        xml.autoconnect(self)
        get = xml.getById
        self.viewer = viewer
        self.lblpos = get('lblpos')
        self.lblzoom = get('lblzoom')
        self.lblcache = get('lblcache')
        self.lbldisp = get('lbldisp')
        self.lblqueue = get('lblqueue')

        get('bluemarble').state = 'down'

    def on_update(self):
        super(MapSettings, self).on_update()
        viewer = self.viewer
        viewermap = viewer.map
        tileserver = viewermap.tileserver
        q_in_len, q_count = len(tileserver.q_in), tileserver.q_count
        self.lblqueue.label = '%d / %d' % ( q_in_len, q_count - q_in_len )
        self.lblzoom.label = '%d' % viewermap.zoom
        lat, lon = viewermap.get_latlon_from_xy(*viewer.center)
        self.lblpos.label = '%.4f %.4f' % (lon, lat)
        self.lbldisp.label = '%d' % viewermap.tilecount

    def on_bingroad_release(self, *l):
        self.viewer.map.provider = 'bing'
        self.viewer.map.maptype = 'roadmap'

    def on_bingsatellite_release(self, *l):
        self.viewer.map.provider = 'bing'
        self.viewer.map.maptype = 'satellite'

    def on_osm_release(self, *l):
        self.viewer.map.provider = 'openstreetmap'
        self.viewer.map.maptype = 'roadmap'

    def on_yahoo_release(self, *l):
        self.viewer.map.provider = 'yahoo'
        self.viewer.map.maptype = 'roadmap'

    def on_bluemarble_release(self, *l):
        self.viewer.map.provider = 'bluemarble'
        self.viewer.map.maptype = 'satellite'

if __name__ == '__main__':
    viewer = MapViewer(size_hint=(1, 1), provider='bluemarble')
    settings = MapSettings(viewer, hide=False)

    win = getWindow()
    win.add_widget(viewer)
    win.add_widget(settings)
    runTouchApp()
