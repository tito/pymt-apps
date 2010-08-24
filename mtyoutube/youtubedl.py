#!/usr/bin/env python 

__all__ = ('YoutubeFormat', 'YoutubeGetFlv', 'YoutubeSearch')

import re
from urllib import urlopen, unquote

YoutubeFormat = {
    '37': {'icon':'FHD',    'desc':'fmt=37 ( HD1080p/MP4/H.264/AAC )'},
    '22': {'icon':'HD',     'desc':'fmt=22 ( HD720p /MP4/H.264/AAC )'},
    '35': {'icon':'HQ',     'desc':'fmt=35 ( HQ     /FLV/H.264/AAC )'},
    '34': {'icon':'LQ',     'desc':'fmt=34 ( LQ     /FLV/H.264/AAC )'},
    '18': {'icon':'SD',     'desc':'fmt=18 ( iPod   /MP4/H.264/AAC )'},
    '6':  {'icon':'OLD',    'desc':'fmt=6  ( OldHQ  /FLV/H.263/MP3 )'},
    '5':  {'icon':'OLD',    'desc':'fmt=5  ( OldLQ  /FLV/H.263/MP3 )'},
    '17': {'icon':'MOB',    'desc':'fmt=17 ( Hmobile/3GP/MPEG4/AAC )'},
    '13': {'icon':'MOB',    'desc':'fmt=13 ( Lmobile/3GP/H.263/AMR )'},
}


def YoutubeGetFlv(url):
    g = re.match('.*watch\?v=(.*)', url)
    if not g:
        print 'ERROR: unable to found watch?v=... in url'
        return None

    id = g.groups()[0].split('&')[0]

    # fetch the page
    datas = urlopen(url).read()

    flvurls = []
    for data in datas.split("\n"):
        g = re.match('.*l_map": "([^"]*)"', data)
        if not g:
            continue
        flvurls = g.groups()[0].split(',')
        break

    flvurls = [x.split('|') for x in flvurls]
    return [(fmt, unquote(value).replace('\\/', '/')) for fmt, value in
            flvurls]

def YoutubeSearch(keyword):
    from xml.dom.minidom import parseString

    url = 'http://gdata.youtube.com/feeds/api/videos?q=%s' % (keyword)
    data = urlopen(url).read()
    dom = parseString(data)
    entries = dom.getElementsByTagName('entry')

    def nodev(entry, name):
        try:
            n = entry.getElementsByTagName(name)[0]
            return n.firstChild.nodeValue
        except:
            return None

    results = []
    for entry in entries:
        result = {}
        result['title'] = nodev(entry, 'title')
        result['thumbnail'] = []
        for link in entry.getElementsByTagName('link'):
            if link.getAttribute('type') != 'text/html':
                continue
            result['url'] = unquote(link.getAttribute('href'))
        for media in entry.getElementsByTagName('media:thumbnail'):
            result['thumbnail'].append({
                'url': media.getAttribute('url'),
                'width': media.getAttribute('width'),
                'height': media.getAttribute('height'),
                'time': media.getAttribute('time')
            })
        results.append(result)
    return results

if __name__ == '__main__':
    #print YoutubeSearch('pymt multitouch')
    import sys
    if len(sys.argv) >= 1:
        result = YoutubeGetFlv(sys.argv[1])
        if result is None:
            print 'Unable to found FLV link in URL'
        else:
            print 'Found', len(result), 'links :'
            for format, url in result:
                if format in YoutubeFormat:
                    print 'Format:', YoutubeFormat[format]['desc']
                print 'URL:', url
    else:
        print 'Usage: youtubedl.py <url>'
