from pymt import *
from lib.boid import *
import ConfigParser
import subprocess

class LauncherButton(MTKineticItem):
    def __init__(self, label, desc, icon, **kwargs):
        super(LauncherButton, self).__init__(**kwargs)
        self._label = Label(label, font_size=24, anchor_x='left',
                           anchor_y='top')
        self._desc = Label(desc, multiline=True, size=(250, 0),
                          font_size=14, anchor_x='left',
                           anchor_y='top', color=(200, 200, 200, 200))
        self._icon = Image(icon)
        self.size = (420, 150)

    def draw(self):
        self._icon.x, self._icon.y = self.x + 10, self.y + 10
        self._label.x, self._label.y = self.x + 140, self.y + 130
        self._desc.x, self._desc.y = self.x + 140, self.y + 90
        set_color(0, 0, 0, .6)
        drawRoundedRectangle(pos=self.pos, size=self.size)
        self._icon.draw()
        self._label.draw()
        self._desc.draw()

def launch_app(path, exe, *largs):
    pymt_logger.info('launcher: Launch %s (path=%s)', exe, path)
    evloop = getEventLoop()
    evloop.stop()
    pymt_logger.info('launcher: evloop.stop() done')
    #stopTouchApp()
    p = subprocess.Popen(args=exe, cwd=path, shell=True)
    pymt_logger.info('launcher: popen() done')
    p.communicate()
    pymt_logger.info('launcher: communicate() done')
    #runTouchApp()
    evloop.start()
    pymt_logger.info('launcher: start() done')

if __name__ == '__main__':

    config = ConfigParser.ConfigParser()
    config.read('config.txt')

    Label('load default font')

    # Window
    m = getWindow()
    m.wallpaper = './data/background.png'

    # Some boid on back
    demo = WanderDemo()
    m.add_widget(demo)
    demo.createBoids(50)

    # Menu
    menu = MTKineticList(title=None, size=(450, m.height),
                        deletable=False, searchable=False,
                        style={'bg-color': (.0, .0, .0, .5)},
                        )
    for section in config.sections():
        label = config.get(section, 'label')
        desc = config.get(section, 'desc')
        icon = config.get(section, 'icon')
        path = config.get(section, 'path')
        exe = config.get(section, 'exec')
        button = LauncherButton(label=label, desc=desc, icon=icon)
        button.push_handlers(on_press=curry(launch_app, path, exe))
        menu.add_widget(button)

    m.add_widget(menu)

    # Start !
    runTouchApp()
