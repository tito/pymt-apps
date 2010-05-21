from pymt import *

'''
 ___________________________
|  | | | |  |  | | | | | |  |
|  | | | |  |  | | | | | |  |
|  |4| | |  |  | | | | | |  |
|  |_| |_|  |  |_| |_| |_|  |
|   |   |   |   |   |   |   |
| 1 | 2 | 3 |   |   |   |   |
|___|___|___|___|___|___|___|
  0 1 2 3 4 5 6 7 8 9 ...
'''

class MTMidiKeyboard(MTScatterWidget):
    def __init__(self, **kwargs):
        super(MTMidiKeyboard, self).__init__(**kwargs)

        kwargs.setdefault('octave', 4)

        self.output = kwargs['output']     # object that will receive note_on &  note_off events
        self.octave = kwargs['octave']
        
        self.color_white = (1,1,1,1)
        self.color_black = (0,0,0,1)
        self.color_down  = (0.5,0.5,0.5,1)
        
        self.key_active = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.keyboard = [ 1, 4, 2, 4, 3, 0, 1 ,4 , 2, 4, 2, 4, 3 ]
        self.keys_mask = [
            { 'note': 0,  'midi':  0, 'zone1': (0,3),   'zone2': (0,2) },    # C
            { 'note': 1,  'midi':  1, 'zone1': (0,0),   'zone2': (2,4) },    # C#
            { 'note': 2,  'midi':  2, 'zone1': (3,6),   'zone2': (4,5) },    # D
            { 'note': 3,  'midi':  3, 'zone1': (0,0),   'zone2': (5,7) },    # D#
            { 'note': 4,  'midi':  4, 'zone1': (6,9),   'zone2': (7,9) },    # E
            { 'note': 6,  'midi':  5, 'zone1': (9,12),  'zone2': (9,11) },    # F
            { 'note': 7,  'midi':  6, 'zone1': (0,0),   'zone2': (11,13) },    # F#
            { 'note': 8,  'midi':  7, 'zone1': (12,15), 'zone2': (13,14) },    # G
            { 'note': 9,  'midi':  8, 'zone1': (0,0),   'zone2': (14,16) },    # G#
            { 'note': 10, 'midi':  9, 'zone1': (15,18), 'zone2': (16,17) },    # A
            { 'note': 11, 'midi': 10, 'zone1': (0,0),   'zone2': (17,19) },    # A#
            { 'note': 12, 'midi': 11, 'zone1': (18,21), 'zone2': (19,21) },    # B
        ]

    def on_touch_down(self, touch):
        x, y = self.to_local(*touch.pos)
        
        if self.test_mask(x,y, 1):
            return True
        #other widgets
        return super(MTMidiKeyboard, self).on_touch_down(touch)
    
    def on_touch_up(self, touch):
        x, y = self.to_local(*touch.pos)

        if self.test_mask(x,y, 0):
            return True
        return super(MTMidiKeyboard, self).on_touch_up(touch)
        
    def test_mask(self, x, y, state):
        step_x = self.width / 23.0
        step_y = self.height / 9.0
        
        for mask in self.keys_mask:
            #zone1
            if y >= step_y and y < 4.0*step_y    and x >= step_x + mask['zone1'][0]*step_x and x <  step_x + mask['zone1'][1]*step_x:
                self.key_active[mask['note']] = state
                if state == 1:
                    self.output.dispatch_event('note_on', mask['midi']+12+self.octave*12)
                else:
                    self.output.dispatch_event('note_off', mask['midi']+12+self.octave*12)
                return True
            
            #zone2
            if y >= 4.0*step_y and y < 8.0*step_y    and x >= step_x + mask['zone2'][0]*step_x and x <  step_x + mask['zone2'][1]*step_x:
                self.key_active[mask['note']] = state
                if state == 1:
                    self.output.dispatch_event('note_on', mask['midi']+12+self.octave*12)
                else:
                    self.output.dispatch_event('note_off', mask['midi']+12+self.octave*12)
                return True
        
        return False

    '''
        w2=2x
       <->
    ____________________________
    |  | | | |  |  | | | | | |  | ^
 h2    |  | | | |  |  | | | | | |  | |       zone2
    |  | | | |  |  | | | | | |  | |
    |  |_| |_|  |  |_| |_| |_|  | | 5*w1
    |   |   |   |   |   |   |   | |
 h1 |   |   |   |   |   |   |   | |       zone1
    |___|___|___|___|___|___|___| v 
    <--->
      w1=3x
    
    ''' 

    def draw(self):
        
        step_x = self.width / 23.0    # 3*7 notes + border
        step_y = self.height / 9.0 
        h1 = 3.0 * step_y
        h2 = 4.0 * step_y
        h  = 7.0 * step_y
        w1 = 3.0 * step_x
        w2 = 2.0 * step_x
        
        #background
        set_color(0.6,0.6,0.6, 1)
        drawRoundedRectangle(
            pos = (0,0),
            size = self.size,
            radius = 10
        )
        
        pos_x = step_x
        pos_y = step_y
        
        for i in range(len(self.keyboard)):
            key = self.keyboard[i]
            if(key == 1):
                if self.key_active[i]:
                    set_color(*self.color_down)
                else:
                    set_color(*self.color_white)
                drawRectangle(
                    pos = (pos_x, pos_y),
                    size = (w1-1, h1)
                )
                drawRectangle(
                    pos = (pos_x, pos_y+h1),
                    size = (w2, h2)
                )
                pos_x += 2.0*step_x
            if(key == 2):
                if self.key_active[i]:
                    set_color(*self.color_down)
                else:
                    set_color(*self.color_white)
                drawRectangle(
                    pos = (pos_x, pos_y),
                    size = (w1-1, h1)
                )
                drawRectangle(
                    pos = (pos_x+step_x, pos_y+h1),
                    size = (step_x, h2)
                )
                pos_x += 2.0*step_x
            if(key == 3):
                if self.key_active[i]:
                    set_color(*self.color_down)
                else:
                    set_color(*self.color_white)
                drawRectangle(
                    pos = (pos_x, pos_y),
                    size = (w1-1, h1)
                )
                drawRectangle(
                    pos = (pos_x+step_x-1, pos_y+h1),
                    size = (2.0*step_x, h2)
                )
                pos_x += 3.0*step_x
            if(key == 4):
                if self.key_active[i]:
                    set_color(*self.color_down)
                else:
                    set_color(*self.color_black)
                drawRectangle(
                    pos = (pos_x, pos_y + h1),
                    size = (w2, h2)
                )
                pos_x += step_x
