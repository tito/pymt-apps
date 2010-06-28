#
# tonepads.py
#
# Author: Mathieu Virbel <tito@bankiz.org>
#
# Copyright (C) 2009 / 2010 Mathieu Virbel
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

import sys
import os
import math
import random
import threading
import time
from pymt import *

try:
    import pymunk
except ImportError:
    print 'Pymunk is required: easy_install pymunk'
    sys.exit(1)

try:
    import pygame
except ImportError:
    print 'Pygame is required'
    sys.exit(1)

try:
    from pygame import midi
except:
    print 'Pygame with midi support is required'

pygame.midi.init()

CONFIG_MIDI_PORT = None
try:
    CONFIG_MIDI_PORT = int(sys.argv[1])
except:
    pass

COLOR_GENERATOR = (0.95294117647058818, 0.52549019607843139, 0.18823529411764706)

MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_STOP = 0xFC

css_physound = '''
basewindow {
    bg-color: rgba(30, 30, 30);
}

button {
    bg-color: rgba(242, 133, 47);
    color: rgba(255, 255, 255);
    draw-border: 1;
    border-radius: 5;
    border-radius-precision: .3;
    draw-alpha-background: 0;
    draw-border: 0;
}

configmidi {
    bg-color: rgba(243, 134, 48);
}

musicgenerator {
    color: rgba(250, 105, 0); /* ball */
    bg-color: rgba(243, 134, 48);
}

musicpad {
    bg-color: rgba(105, 210, 231);
    color: rgba(250, 105, 0);
}

musicpadtoggle {
    bg-color: rgba(210, 105, 231);
}

musicpadnocollision {
    bg-color: rgba(105, 105, 105);
}

musicpadtogglenocollision {
    bg-color: rgba(210, 105, 105);
}
'''
css_add_sheet(css_physound)
css_reload()

# ball registry (pymunk object <-> app object)
ball_registry = {}

# Accelerated drawcircle function
data_path = os.path.join(os.path.dirname(__file__), 'data')
image_circle32 = Image(os.path.join(data_path, 'circle32.png'))
image_circle64 = Image(os.path.join(data_path, 'circle64.png'))
image_circle128 = Image(os.path.join(data_path, 'circle128.png'))

def drawCircle2(pos=(0, 0), radius=10.):
    image = image_circle32
    if radius > 32:
        image = image_circle128
    elif radius > 16:
        image = image_circle64
    size = Vector(image.size) / image.width * radius * 2
    pos = pos[0] - size[0] / 2., pos[1] - size[1] / 2.
    with gx_blending:
        drawTexturedRectangle(texture=image.texture, pos=pos, size=size)


class MidiClock(threading.Thread):
    '''Internal thread that control the midi clock.
    Clock are not really used from now.
    '''

    tempo   = 140.0
    dev     = None

    def __init__(self):
        threading.Thread.__init__(self)
        self._running = True
        self.start()

    def __del__(self):
        self.quit()

    def run(self):
        while self._running:
            spb = 60.0 / self.tempo
            spc = spb / 24.0
            usec = spc * 1000000
            self.send(MIDI_CLOCK)
            time.sleep(spc)

    def quit(self):
        self._running = False

    def startClock(self):
        self.send(MIDI_START)

    def stopClock(self):
        self.send(MIDI_STOP)

    def send(self, *args):
        pass


class RtMidiClock(MidiClock):
    '''Layer on MidiClock, with implementation of send() + specific midi
    functions implemented.'''
    def __init__(self):
        self.lock = threading.Lock()
        self.dev = None
        MidiClock.__init__(self)

    def setDevice(self, i=None):
        self.lock.acquire()
        if self.dev is not None:
            self.dev.close()
        self.dev = midi.Output(i)
        # TODO make it customizable
        if sys.platform == 'win32':
            self.dev.set_instrument(82)
        self.lock.release()

    def send(self, *args):
        if self.dev is None:
            return
        self.lock.acquire()
        self.dev.write_short(*args)
        self.lock.release()

    def noteon(self, note, channel=0, velocity=90):
        v = (9 << 4) + channel
        self.send(v, note, velocity)

    def noteoff(self, note, channel=0, velocity=90):
        v = (8 << 4) + channel
        self.send(v, note, velocity)


class MusicPad(MTWidget):
    '''This is the base for the Pad.

    The pad is automaticly created by a MusicPlane, when 2 finger are close
    enough, and not yet used by another MusicPad.

    The pad will stay on the screen, even if no touch are attached to it.
    When the corner are too close (mean < MusicPad.min), the pad will remove
    himself from the MusicPlane.

    '''

    min = 60
    max = 500

    def __init__(self, **kwargs):
        if self.__class__ == MusicPad:
            raise NotImplementedError, 'class MusicPad is abstract'

        self.t1         = kwargs.get('t1')
        self.t2         = kwargs.get('t2')
        self.space      = kwargs.get('space')
        self.midi       = kwargs.get('midi')

        self.drawback   = True
        self.backdt     = 0
        self.image      = Image(image_circle32)
        self.imageback  = Image(image_circle128)

        super(MusicPad, self).__init__(**kwargs)

        self.radius     = self.image.width / 2.
        self.to_delete  = False

        # cache position of touches
        self.v1         = Vector(self.t1.pos)
        self.v2         = Vector(self.t2.pos)

        # create physic
        self.line       = None
        self.body       = pymunk.Body(pymunk.inf, pymunk.inf)
        self.on_physic()

        # mark touchs
        self.t1.userdata['mg.pad'] = self
        self.t2.userdata['mg.pad'] = self

        # music
        self.dt         = 999.
        self.noteon     = False
        self.note       = 0
        self.notelen    = 0.15
        self.notechannel = 0
        self.oldnote    = 0

        # custom properties
        self.delete_ball    = False


    def collide_point1(self, x, y):
        d = Vector(self.v1).distance(Vector(x, y))
        if d < self.radius:
            return True
        return False

    def collide_point2(self, x, y):
        d = Vector(self.v2).distance(Vector(x, y))
        if d < self.radius:
            return True
        return False

    def on_touch_down(self, touch):
        if self.t1 is None and self.collide_point1(touch.x, touch.y):
            self.t1 = touch
            touch.userdata['mg.pad'] = self
            return True
        if self.t2 is None and self.collide_point2(touch.x, touch.y):
            self.t2 = touch
            touch.userdata['mg.pad'] = self
            return True
        return super(MusicPad, self).on_touch_down(touch)

    def kill(self):
        self.soundoff()
        self.parent.remove_pad(self)

    def on_update(self):
        self.dt += getFrameDt()
        touchs = getCurrentTouches()
        if self.t1 is not None:
            self.v1 = Vector(self.to_widget(*self.t1.pos))
            if self.t1 not in touchs:
                self.t1 = None

        if self.t2 is not None:
            self.v2 = Vector(self.to_widget(*self.t2.pos))
            if self.t2 not in touchs:
                self.t2 = None

        self.to_delete = False
        if self.v1.distance(self.v2) < MusicPad.min:
            self.to_delete = True
            if self.t1 is None and self.t2 is None:
                self.kill()
                return

        if self.dt >= self.notelen and self.noteon:
            self.soundoff()
            return

        if self.oldnote != self.calculate_note() and self.noteon:
            self.soundoff()
            self.soundon(self.notechannel)

        self.on_physic()

    def on_physic(self):
        if self.line:
            self.space.remove(self.line)
            self.line = None
        if self.to_delete:
            return
        self.pos = (self.v1 + self.v2) / 2.
        self.body.position = self.pos
        self.line = pymunk.Segment(self.body, self.v1 - self.pos, self.v2 - self.pos, 5.0)
        self.line.elasticity = 1
        self.space.add(self.line)

    def draw(self):
        cn = self.style.get('bg-color') # normal color
        ct = self.style.get('color')    # selected color
        if not self.to_delete:

            if self.drawback:
                # background
                self.backdt = boundary((self.dt - self.notelen) / 3., 0, 0.2)
            else:
                self.backdt += getFrameDt()
            if self.backdt <= .2:
                set_color(cn[0], cn[1], cn[2], .2 - self.backdt)
                drawCircle2(pos=self.pos, radius=Vector(self.pos).distance(self.v1))

            # bat
            if self.noteon:
                set_color(ct[0], ct[1], ct[2], .8)
                w = 5.
            else:
                set_color(cn[0], cn[1], cn[2], .8)
                w = 1.
            drawLine((self.v1.x, self.v1.y, self.v2.x, self.v2.y), width=w)

        # corner
        set_color(cn[0], cn[1], cn[2])
        drawCircle2(pos=self.v1, radius=self.radius)
        drawCircle2(pos=self.v2, radius=self.radius)

        # text
        if (self.t1 or self.t2) and not self.to_delete:
            drawLabel(label=str(self.calculate_note()), pos=self.pos, font_size=24)

    def calculate_note(self):
        '''Use distance as base to calculate note.
        1. constrain min < distance <= max 
        2. to 0 < d <= 1
        3. and calculate the 0 < d <= 128
        '''
        smin = MusicPad.min
        smax = MusicPad.max
        d = Vector(self.v1).distance(Vector(self.v2))
        d = (boundary(d, smin, smax) - smin) / (smax - smin)
        return 128 - int(d * 128)

    def soundon(self, channel):
        '''Play the note'''
        if not self.noteon:
            note = self.calculate_note()
            self.noteon = True
            self.note   = note
            self.notechannel = channel
            self.midi.noteon(note, channel)
            self.oldnote = note
        self.dt = 0

    def soundoff(self):
        '''Stop the note'''
        if self.noteon:
            self.noteon = False
            self.midi.noteoff(self.note, self.notechannel)

    def on_collide(self, obj):
        if self.delete_ball:
            self.parent.delete_queue.append(obj)
        return False


class MusicPadNormal(MusicPad):
    def __init__(self, **kwargs):
        super(MusicPadNormal, self).__init__(**kwargs)

    def on_collide(self, obj):
        channel = ball_registry[obj].channel
        self.soundon(channel)
        super(MusicPadNormal, self).on_collide(obj)
        return True


class MusicPadNoCollision(MusicPadNormal):
    def __init__(self, **kwargs):
        super(MusicPadNoCollision, self).__init__(**kwargs)

    def on_collide(self, obj):
        super(MusicPadNoCollision, self).on_collide(obj)
        return False


class MusicPadToggle(MusicPad):
    def __init__(self, **kwargs):
        super(MusicPadToggle, self).__init__(**kwargs)
        self.notelen = 9999999.

    def on_collide(self, obj):
        channel = ball_registry[obj].channel
        if self.noteon:
            self.soundoff()
        else:
            self.soundon(channel)
        super(MusicPadToggle, self).on_collide(obj)
        return True

    def on_update(self):
        self.drawback = self.noteon
        super(MusicPadToggle, self).on_update()


class MusicPadToggleNoCollision(MusicPadToggle):
    def __init__(self, **kwargs):
        super(MusicPadToggleNoCollision, self).__init__(**kwargs)
        self.padl_last = []
        self.padl_current = []

    def on_update(self):
        self.padl_last = self.padl_current
        self.padl_current = []
        super(MusicPadToggleNoCollision, self).on_update()

    def on_collide(self, obj):
        self.padl_current.append(obj)
        if obj in self.padl_last:
            return False
        super(MusicPadToggleNoCollision, self).on_collide(obj)
        return False


class MusicGenerator(MTDragable):
    '''A circle that generate balls :)'''
    def __init__(self, space, **kwargs):
        super(MusicGenerator, self).__init__(**kwargs)
        self.image      = Image(image_circle32)
        self.radius     = self.image.width / 2.
        self.balls      = []
        self.space      = space
        self.dt         = 0
        self.curtouch   = None
        self.channel    = 0
        self.to_delete   = False

    def generate(self):
        mass = 1
        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0,0))
        body = pymunk.Body(mass, inertia)
        body.position = self.x, self.y
        #body.apply_impulse(1)
        shape = pymunk.Circle(body, self.radius, (0,0))
        shape.elasticity = 0.95
        self.space.add(body, shape)
        self.balls.append(shape)
        ball_registry[shape] = self
        body.apply_impulse((0, -500))

    def collide_point(self, x, y):
        d = Vector(x, y).distance(Vector(self.pos))
        if d < self.radius * 2:
            return True
        return False

    def update_channel(self, d):
        d = boundary(int((d - self.radius) / 20.), 0, 16)
        self.to_delete = False
        if d == 16:
            self.to_delete = True
            d = 15
        self.channel = d

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y) and \
           touch.is_double_tap and self.curtouch is None:
            print 'distance=', touch.double_tap_distance, 'time=', touch.double_tap_time
            touch.grab(self)
            self.curtouch = touch.pos
            self.update_channel(Vector(touch.pos).distance(Vector(self.pos)))
            return True
        return super(MusicGenerator, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            self.curtouch = touch.pos
            self.update_channel(Vector(touch.pos).distance(Vector(self.pos)))
            return True
        return super(MusicGenerator, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            touch.ungrab(self)
            self.curtouch = None
            if self.to_delete:
                self.parent.remove_widget(self)
            return True
        return super(MusicGenerator, self).on_touch_up(touch)

    def on_update(self):
        self.dt += getFrameDt()
        if self.dt >= 1:
            self.dt = 0
            self.generate()

        # kills balls
        for ball in self.parent.delete_queue:
            if ball in self.balls:
                self.space.remove(ball)
                self.balls.remove(ball)

    def draw(self):
        set_color(*self.style.get('bg-color'))
        drawCircle2(pos=self.pos, radius=self.radius * 2)

        if self.curtouch:
            drawLine((self.x, self.y, self.curtouch[0], self.curtouch[1]))
            if self.to_delete:
                label = 'DEL'
            else:
                label = str(self.channel)
            drawLabel(label=label, pos=self.pos, font_size=20)

        set_color(*self.style.get('color'))
        for ball in self.balls:
            p = Vector(ball.body.position.x, ball.body.position.y)
            #if p[0] + ball.radius < 0 or p[0] - ball.radius > w.width \
            #   or p[1] + ball.radius < 0:
            if p[1] < -9999:
                self.space.remove(ball)
                self.balls.remove(ball)
            else:
                drawCircle2(pos=p, radius=ball.radius)


class MusicPlane(MTScatterPlane):
    '''The music plane !'''
    def __init__(self, **kwargs):
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_rotation', False)
        super(MusicPlane, self).__init__(**kwargs)

        self.dt = 0
        self.delete_queue = []
        self.pads = []

        # initialize physics
        pymunk.init_pymunk()
        space = pymunk.Space()
        #space.gravity = (0.0, -900.0)
        space.gravity = (0.0, 0.0)
        space.set_default_collision_handler(self.collide_found, None, None, None)
        self.space = space

    def collide_found(self, space, arbitrer, *largs):
        ball, seg = arbitrer.shapes
        if type(ball) == pymunk.Segment and type(seg) == pymunk.Circle:
            ball, seg = seg, ball
        if type(seg) != pymunk.Segment or type(ball) != pymunk.Circle:
            return True

        for w in self.pads:
            if w.line != seg:
                continue
            return w.on_collide(ball)

        # no pad found ?
        return True

    def update_pads(self):
        touchs = getCurrentTouches()
        freetouch = [x for x in touchs if not 'mg.pad' in x.userdata]
        restart = False
        for touch1 in freetouch:
            d = 999
            touch2 = None
            for b in freetouch:
                if touch1 == b:
                    continue
                e = Vector(touch1.x, touch1.y).distance(Vector(b.x, b.y))
                if e < d:
                    d = e
                    touch2 = b

            if touch2 is not None:
                self.create_pad(touch1, touch2)
                restart = True
                break

        # recursive.
        if restart:
            self.update_pads()

    def create_pad(self, p1, p2):
        cls = MusicPadNormal
        pad_type = self.parent.pad_type
        if 'type-toggle' in pad_type and 'type-nocollision' in pad_type:
            cls = MusicPadToggleNoCollision
        elif 'type-toggle' in pad_type:
            cls = MusicPadToggle
        elif 'type-nocollision' in pad_type:
            cls = MusicPadNoCollision
        pad = cls(t1=p1, t2=p2, space=self.space, midi=self.parent.midi)
        if 'type-killball' in pad_type:
            pad.delete_ball = True
        self.pads.append(pad)
        self.add_widget(pad)

    def remove_pad(self, pad):
        if pad in self.pads:
            self.pads.remove(pad)
        self.remove_widget(pad)

    def create_generator(self, pos=(0, 0)):
        gen = MusicGenerator(self.space, pos=pos)
        self.add_widget(gen)

    def draw(self):
        w = self.get_parent_window()

        # create pads
        self.update_pads()

        # advance in time
        self.delete_queue = []
        self.space.step(getFrameDt())
        for ball in self.delete_queue:
            if ball in ball_registry:
                del ball_registry[ball]

    def on_touch_down(self, touch):
        super(MusicPlane, self).on_touch_down(touch)
        return False


class ConfigMidi(MTBoxLayout):
    '''UI of midi selection port'''
    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('spacing', 10)
        super(ConfigMidi, self).__init__(**kwargs)
        self.selected       = -1
        self.selectedname   = ''

    def select(self, index, *largs):
        try:
            self.parent.midi.setDevice(index)
            self.selected       = index
            self.selectedname   = midi.get_device_info(index)[1]
        except:
            raise
        self.refresh()

    def refresh(self):
        self.children = SafeList()
        for index in xrange(midi.get_count()):
            info = midi.get_device_info(index)
            interf, name, input, output, opened = info
            if output <= 0:
                continue
            btn = MTToggleButton(label=name, size=(200, 30))
            btn.size = btn.label_obj.content_width + 20, 30
            btn.push_handlers(on_press=curry(self.select, index))
            self.add_widget(btn)
            if self.selected == index and \
                self.selectedname == name:
                btn.state = 'down'

    def on_update(self):
        w = self.get_parent_window()
        if w:
            self.center = Vector(w.size) / 2.
        super(MTBoxLayout, self).on_update()

    def draw(self):
        c = self.style.get('bg-color')
        c[3] = .5
        set_color(*c)
        drawRoundedRectangle(pos=self.pos, size=self.size)


class UISelector(MTBoxLayout):

    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('padding', 10)
        kwargs.setdefault('spacing', 10)
        super(UISelector, self).__init__(**kwargs)

        self.btns = []
        self.btns.append(MTToggleButton(
            label='Toggle', cls='type-toggle', size=(100, 30)))
        self.btns.append(MTToggleButton(
            label='No collision', cls='type-nocollision', size=(100, 30)))
        self.btns.append(MTToggleButton(
            label='Kill balls', cls='type-killball', size=(100, 30)))

        for b in self.btns:
            b.push_handlers(on_press=curry(self.on_button_press, b))
            self.add_widget(b)

    def on_button_press(self, button, *largs):
        self.parent.pad_type = []
        for b in self.btns:
            if b.state == 'down':
                self.parent.pad_type.append(b.cls)

    def on_update(self):
        w = self.get_parent_window()
        self.center = (w.width / 2., w.height - self.height)
        super(MTBoxLayout, self).on_update()

    def draw(self):
        set_color(COLOR_GENERATOR[0], COLOR_GENERATOR[1], COLOR_GENERATOR[2], .5)
        drawCSSRectangle(pos=self.pos, size=self.size, style=self.style)


class UITools(MTBoxLayout):

    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('padding', 10)
        kwargs.setdefault('spacing', 10)
        super(UITools, self).__init__(**kwargs)

        # buttons
        self.b_move = MTToggleButton(label='Lock move', size=(100, 30))
        self.b_move.push_handlers(on_press=curry(self._on_move_pressed, self.b_move))
        self.add_widget(self.b_move)

        self.b_gen = MTButton(label='Create generator', size=(130, 30))
        self.b_gen.push_handlers(on_press=curry(self._on_gen_pressed, self.b_gen))
        self.add_widget(self.b_gen)

        self.b_midi = MTToggleButton(label='Midi', size=(100, 30))
        self.b_midi.push_handlers(on_press=curry(self._on_midi_pressed, self.b_midi))
        self.add_widget(self.b_midi)



    def _on_midi_pressed(self, btn, *largs):
        if btn.state == 'down':
            self.parent.ui_midi.visible = True
        else:
            self.parent.ui_midi.visible = False
        if self.parent.ui_midi.visible:
            self.parent.ui_midi.refresh()

    def _on_move_pressed(self, btn, *largs):
        if btn.state == 'down':
            self.parent.plane.do_translation = False
        else:
            self.parent.plane.do_translation = True

    def _on_gen_pressed(self, btn, *largs):
        w = self.get_parent_window()
        x, y = self.parent.plane.to_local(*(Vector(w.size) / 2.))
        self.parent.plane.create_generator(pos=(x, y))
        return True

    def on_update(self):
        w = self.get_parent_window()
        self.center = (w.width / 2., self.height)
        super(MTBoxLayout, self).on_update()

    def draw(self):
        set_color(COLOR_GENERATOR[0], COLOR_GENERATOR[1], COLOR_GENERATOR[2], .5)
        drawCSSRectangle(pos=self.pos, size=self.size, style=self.style)


class MusicUI(MTWidget):
    '''Initial UI that handle Midi + Plane + UI'''
    def __init__(self, **kwargs):
        super(MusicUI, self).__init__(**kwargs)
        self.plane = MusicPlane()
        self.add_widget(self.plane)

        self.ui_tools = UITools()
        self.add_widget(self.ui_tools)

        self.ui_midi = ConfigMidi()
        self.add_widget(self.ui_midi)
        self.ui_midi.visible = False

        # type
        self.pad_type = []
        self.add_widget(UISelector())

        # initialize audio
        self.midi = RtMidiClock()
        if CONFIG_MIDI_PORT is not None:
            self.midi.setDevice(CONFIG_MIDI_PORT)

    def quit(self):
        self.midi.quit()

if __name__ == '__main__':
    w = MTWindow()
    mp = MusicUI()
    mp.plane.create_generator(pos=Vector(w.size) / 2.)
    w.add_widget(mp)
    runTouchApp()
    mp.quit()
