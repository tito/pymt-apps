# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Touch Sequencer'
PLUGIN_AUTHOR = 'Remi Pauchet'
PLUGIN_DESCRIPTION = 'Play!'

'''


Midi notes:
http://www.harmony-central.com/MIDI/Doc/table2.html

midi instruments:
http://fr.wikipedia.org/wiki/General_MIDI
http://en.wikipedia.org/wiki/File:GMStandardDrumMap.gif

TODO:
- volume mixer
- patterns prog
- instruments
- load save (pickle)
- better css
- change track name

'''

from pymt import *
import pygame.midi
import re
import time


css = '''

* {
    /* foreground/text color */
    color: rgba(0, 0, 0, 255);

    /* color when something is pushed TODO: change everywhere this is used, becsue it will be foregroudn color when state is down*/
    color-down: rgba(50,50,50, 128);
    
    /*new way of background color when somethign is pushed*/
    bg-color-down: rgba(50,50,50, 128);

    /* background color of widget */
    bg-color: rgba(100,100,100, 240);

    /* fonts */
    font-size: 13;
    font-name: 'Verdana,Liberation Sans,Bitstream Vera Sans,Free Sans,Arial, Sans';
    font-weight: normal; /* normal, bold, italic, bolditalic */
			   

    /* borders */
    border-width: 1.5;
    border-radius: 0;
    border-radius-precision: 1;
    draw-border: 0;

    /* background alpha layer */
    draw-background: 1;
    draw-alpha-background: 1;
    alpha-background: 1 1 0.5 0.5;

    /* text shadow */
    draw-text-shadow: 0;
    text-shadow-color: rgba(22, 22, 22, 63);
    text-shadow-position: -1 1;
}

'''

css_add_sheet(css)



keys = [ 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B' ] # the chromatic scale

instruments = [
#  Piano
	"Acoustic Grand Piano",
	"Bright Acoustic Piano",
	"Electric Grand Piano",
	"Honkytonk Piano",
	"Electric Piano 1",
	"Electric Piano 2",
	"Harpsichord",
	"Clavi",
#  Chromatic Percussion
	"Celesta",
	"Glockenspiel",
	"Music Box",
	"Vibraphone",
	"Marimba",
	"Xylophone",
	"Tubular Bells",
	"Dulcimer",
#  Organ 
	"Drawbar Organ",
	"Percussive Organ",
	"Rock Organ",
	"Church Organ",
	"Reed Organ",
	"Accordion",
	"Harmonica",
	"Tango Accordion",
#  Guitar 
	"Acoustic Guitar (nylon)",
	"Acoustic Guitar (steel)",
	"Electric Guitar (jazz)",
	"Electric Guitar (clean)",
	"Electric Guitar (muted)",
	"Overdriven Guitar",
	"Distortion Guitar",
	"Guitar Harmonics",
#  Bass 
	"Acoustic Bass",
	"Electric Bass (finger)",
	"Electric Bass (pick)",
	"Fretless Bass",
	"Slap Bass 1",
	"Slap Bass 2",
	"Synth Bass 1",
	"Synth Bass 2",
#  Strings 
	"Violin",
	"Viola",
	"Cello",
	"Contrabass",
	"Tremolo Strings",
	"Pizzicato Strings",
	"Orchestral Harp",
	"Timpani",
#  Ensemble 
	"String Ensemble 1",
	"String Ensemble 2",
	"SynthStrings 1",
	"SynthStrings 2",
	"Choir Aahs",
	"Voice Oohs",
	"Synth Voice",
	"Orchestra Hit",
#  Brass 
	"Trumpet",
	"Trombone",
	"Tuba",
	"Muted Trumpet",
	"French Horn",
	"Brass Section",
	"SynthBrass 1",
	"SynthBrass 2",
#  Reed 
	"Soprano Sax",
	"Alto Sax",
	"Tenor Sax",
	"Baritone Sax",
	"Oboe",
	"English Horn",
	"Bassoon",
	"Clarinet",
#  Pipe 
	"Piccolo",
	"Flute",
	"Recorder",
	"Pan Flute",
	"Blown Bottle",
	"Shakuhachi",
	"Whistle",
	"Ocarina",
#  Synth Lead 
	"Lead 1 (square)",
	"Lead 2 (sawtooth)",
	"Lead 3 (calliope)",
	"Lead 4 (chiff)",
	"Lead 5 (charang)",
	"Lead 6 (voice)",
	"Lead 7 (fifths)",
	"Lead 8 (bass + lead)",
#  Synth Pad 
	"Pad 1 (new age)",
	"Pad 2 (warm)",
	"Pad 3 (polysynth)",
	"Pad 4 (choir)",
	"Pad 5 (bowed)",
	"Pad 6 (metallic)",
	"Pad 7 (halo)",
	"Pad 8 (sweep)",
#  Synth FM 
	"FX 1 (rain)",
	"FX 2 (soundtrack)",
	"FX 3 (crystal)",
	"FX 4 (atmosphere)",
	"FX 5 (brightness)",
	"FX 6 (goblins)",
	"FX 7 (echoes)",
	"FX 8 (sci-fi)",
#  Ethnic Instruments 
	"Sitar",
	"Banjo",
	"Shamisen",
	"Koto",
	"Kalimba",
	"Bag Pipe",
	"Fiddle",
	"Shanai",
#  Percussive Instruments 
	"Tinkle Bell",
	"Agogo",
	"Steel Drums",
	"Woodblock",
	"Taiko Drum",
	"Melodic Tom",
	"Synth Drum",
	"Reverse Cymbal",
#  Sound Effects 
	"Guitar Fret Noise",
	"Breath Noise",
	"Seashore",
	"Bird Tweet",
	"Telephone Ring",
	"Helicopter",
	"Applause",
	"Gunshot"
]

scales = {
	 'Major'           : [ 1, 1, .5, 1, 1, 1, .5],
	 'Pentatonic Major': [ 1, 1, 1.5, 1, 1.5],
	 'Blues Major'     : [ 1.5, 1, .5, .5, 1, 1.5],
	 'Minor'           : [ 1, .5, 1, 1, .5, 1, 1],
	 'Melodic Minor'   : [ 1, .5, 1, 1, 1, 1, .5],
	 'Harmonic Minor'  : [ 1, .5, 1, 1, .5, 1.5, .5],
	 'Pentatonic Minor': [ 1.5, 1, 1, .5, .5],
	 'Blues Minor'     : [ 1.5, 1, .5, .5, 1.5, 1]
}


intro = [
 [1,1,0,0,0,0,0,0,1,0,1,0,1,1,1],
 [1,0,1,0,1,0,1,0,1,1,1,0,0,1,0],
 [1,1,0,0,1,1,1,0,1,1,1,0,0,1,0],
 [1,0,0,0,0,0,1,0,1,0,1,0,0,1,0],
 [1,0,0,0,1,1,1,0,1,0,1,0,0,1,0]
]



class MusicButtonMatrix(MTButtonMatrix):
    def __init__(self, **kwargs):
        super(MusicButtonMatrix, self).__init__(**kwargs)
        self.col = 0
        self.dl = {}

    def draw_tile(self, i, j):
        if self.matrix[i][j] == 0:
            set_color(*self.buttoncolor)
        elif self.matrix[i][j] == 1:
            set_color(*self.downcolor)

        w, h = self.size
        mw, mh = self.matrix_size
        dls = self.dl

        # calculate the index of display list to use
        idx = j * mw + i
        if not idx in dls:
            dls[idx] = GlDisplayList(mode='execute')

        # use the display list
        dl = dls[idx]

        # calculate position (used for dl, and for alpha)
        p = w / mw * i + self.x, h / mh * j + self.y
        s = w / mw - self.border, h / mh - self.border

        # create or compile the display list
        if not dl.is_compiled():
            with dl:
                drawRoundedRectangle(pos=p, size=s)
        else:
            dl.draw()

        # draw an alpha for current row
        if i == self.col:
            set_color(1, 1, 1, .2)
            drawRoundedRectangle(pos=p, size=s)

class Track():
	'''
	Object that represent one track. This is a matrix for the notes played, the 
	notes of the selected scale, a midi channel and a midi instrument
	'''
	def __init__(self, **kwargs):
		'''Arguments: 
		 name: name of the track
		 base_note: name of the base note of the scale
		 scale: name of the musical scale used
		 channel: midi channel of the track, 9 is used for drums
		 instrument: name of the midi instrument
		'''
		
		self.reset()
		
		#parse arguments
		self.name  = kwargs['name']
		self.base_note_name = kwargs['base_note']
		self.scale = kwargs['scale']
		self.tones = scales[self.scale]
		self.channel    = kwargs['channel']
		if self.channel == 9: #9 reserverd for drums
			self.instrument = 0
			self.instrument_name = 'Drum'
		else :
			self.instrument = instruments.index(kwargs['instrument'])
			self.instrument_name = kwargs['instrument']
		
		self.muted = False
		self.solo = False
		
		#calc midi base note & find the key name
		r = re.match("(A|B|C|D|E|F|G#{0,1})(\d{1})", self.base_note_name)
		self.key = r.group(1)
		self.base_note = keys.index(self.key) + 12*(int(r.group(2))+1)
		
		print "Track %s | midi channel %s | instrument %s (%s)" % (self.name, self.channel, self.instrument_name, self.instrument)
		print "     | scale %s | base note %s (%s) | key %s" % ( self.scale, self.base_note_name, self.base_note, self.key)
		
		self.notes = [0 for i in range(self.gridy)] #notes in the scale
		self.note_names = [0 for i in range(self.gridy)]
		
		self.process_scale()
		
	
	def reset(self, *largs):
		'''Clear the notes of the track
		'''
		self.gridx = 16
		self.gridy = 16
		self.grid = [[0 for i in range(self.gridx)] for i in range(self.gridy)]
	
	def change_key(self,x, *largs):
		'''Change the root note of the scale
		'''
		self.key = keys[x]
		self.process_scale()
	
	def change_scale(self,x, *largs):
		'''Change the scale
		'''
		self.scale = x
		self.tones = scales[self.scale]
		self.process_scale()
		
	def change_instrument(self,x, *largs):
		'''Change the midi instrument
		'''
		self.instrument_name = x
		self.instrument = instruments.index(x)
		print '><', x, largs
		print "instrument %s (%d)" % (self.instrument_name, self.instrument)
	
	def process_scale(self):
		'''Calculate the notes of the scale
		'''
		self.notes[0] = self.base_note +keys.index(self.key)
		self.note_names[0] = self.key
		for i in range(1,self.gridy):
			self.notes[i] =  int(self.notes[i-1] + self.tones[(i-1) % len(self.tones)]*2)
			self.note_names[i] = keys[(self.notes[i] - self.base_note) % 12]
		print "Scale : %s" % self.note_names

class Sequencer(MTWidget):
	def __init__(self, **kwargs):
		super(Sequencer, self).__init__(**kwargs)
		
		self.bpm = 180
		self.paused = False
		self.gridx = 16
		self.gridy = 16
		self.stepx = 1
		self.stepy = 1
		self.currentrow = 0
		self.latency = 0.2 # in seconds
		self.ts_save = time.time()
		self.orig = self.ts_save
		self.master = 0
		self.filename = 'default'
		
		#midi init
		pygame.midi.init()
		
		c = pygame.midi.get_count()
		print "%s midi devices found" % c
		for i in range(c):
			print "%s name: %s input: %s output: %s opened: %s" % (pygame.midi.get_device_info(i))
		self.device = pygame.midi.get_default_output_id()
		print "Default is %s" % self.device
		
		self.midi_out = pygame.midi.Output(self.device, latency=0.1)
		
		self.lead1 = Track(name='Lead 1', channel = 0, scale = 'Major', base_note = 'C3', instrument = 'Acoustic Grand Piano')
		self.lead2 = Track(name='Lead 2', channel = 1, scale = 'Major', base_note = 'C3', instrument = 'Harpsichord')
		self.lead3 = Track(name='Lead 3', channel = 2, scale = 'Major', base_note = 'C3', instrument = 'SynthStrings 1')
		self.bass = Track(name='Bass',   channel = 3, scale = 'Major', base_note = 'C2', instrument = 'Electric Bass (pick)')
		self.drum = Track(name='Drum',   channel = 9, scale = 'Major', base_note = 'C3')
		
		self.tracks = [ self.lead1, self.lead2, self.lead3, self.bass, self.drum]
		self.current_track = self.lead1 
		
		#set midi instrument
		for track in self.tracks:
			self.midi_out.set_instrument(track.instrument, channel=track.channel)
		
		self.create_menu()
		
		self.intro()
		
		#go for it !
		getClock().schedule_once(self.play, 60.0/self.bpm)

	def intro(self):
		for y in range(5):
			for x in range(15):
				self.current_track.grid[x][y+6] = intro[4-y][x]
		

	def change_key(self,x, *largs):
		self.current_track.change_key(x)
	
	def change_scale(self,x, *largs):
		self.current_track.change_scale(x)
		
	def change_instrument(self,x, *largs):
		self.current_track.change_instrument(x)
		print "changing intrument '%s' track '%s' midi %i channel %i" % (x, self.current_track.name, self.current_track.instrument, self.current_track.channel)
		self.midi_out.set_instrument(self.current_track.instrument, channel=self.current_track.channel)

	def create_menu(self):
		xml = '''<?xml version="1.0" encoding="UTF-8"?>
		<MTBoxLayout id="'menu'" orientation="'vertical'" invert_y="True">
		 <MTGridLayout cols="2" size_hint='(None,None)'>
		  <MTLabel label="'Bpm:'" size="(120, 30)"/>
		  <MTSlider id="'slider_tempo'" min="50" max="300" value="180" orientation="'horizontal'" value_show="True" size="(200, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="3" size_hint='(None,None)'>
		  <MTLabel label="'Transpose:'" size="(120, 30)"/>
		  <MTButton id="'button_transpose_up'" label="'Up'" size="(100, 30)"/>
		  <MTButton id="'button_transpose_down'" label="'Down'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="9" size_hint='(None,None)'>
		  <MTLabel label="'Scale'" size="(120, 30)"/>
		  <MTButton id="'scale_Major'" label="'Major'" size="(100, 30)"/>
		  <MTButton id="'scale_Pentatonic Major'" label="'Pentatonic Major'" size="(100, 30)"/>
		  <MTButton id="'scale_Blues Major'" label="'Blues Major'" size="(100, 30)"/>
		  <MTButton id="'scale_Minor'" label="'Minor'" size="(100, 30)"/>
		  <MTButton id="'scale_Melodic Minor'" label="'Melodic Minor'" size="(100, 30)"/>
		  <MTButton id="'scale_Harmonic Minor'" label="'Harmonic Minor'" size="(100, 30)"/>
		  <MTButton id="'scale_Pentatonic Minor'" label="'Pentatonic Minor'" size="(100, 30)"/>
		  <MTButton id="'scale_Blues Minor'" label="'Blues Minor'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="13" size_hint='(None,None)'>
		  <MTLabel label="'Key'" size="(120, 30)"/>
		  <MTButton id="'key_0'"  label="'C'"  size="(50, 30)"/>
		  <MTButton id="'key_1'"  label="'C#'" size="(50, 30)"/>
		  <MTButton id="'key_2'"  label="'D'"  size="(50, 30)"/>
		  <MTButton id="'key_3'"  label="'D#'" size="(50, 30)"/>
		  <MTButton id="'key_4'"  label="'E'"  size="(50, 30)"/>
		  <MTButton id="'key_5'"  label="'F'"  size="(50, 30)"/>
		  <MTButton id="'key_6'"  label="'F#'" size="(50, 30)"/>
		  <MTButton id="'key_7'"  label="'G'"  size="(50, 30)"/>
		  <MTButton id="'key_8'"  label="'G#'" size="(50, 30)"/>
		  <MTButton id="'key_9'"  label="'A'"  size="(50, 30)"/>
		  <MTButton id="'key_10'" label="'A#'" size="(50, 30)"/>
		  <MTButton id="'key_11'" label="'B'"  size="(50, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="2" size_hint='(None,None)'>
		  <MTLabel label="'Instrument'" size="(250, 30)"/>
		  <MTButton id="'change_inst'" label="'Change'" size="(100, 30)"/>
		 </MTGridLayout>
		 <MTGridLayout cols="1"  size_hint='(None,None)'>
		  <MTButton id="'button_clear'" label="'Clear'" size="(100, 30)"/>
		 </MTGridLayout>
		</MTBoxLayout>
		'''

		w = XMLWidget(xml=xml)
		
		self.add_widget(MTSidePanel(layout=w.root))

		w.getById('slider_tempo').connect('on_value_change', self.update_bpm)
		w.getById('button_clear').connect('on_press', self.reset)
		w.getById('button_transpose_up').connect('on_press', self.transpose_up)
		w.getById('button_transpose_down').connect('on_press', self.transpose_down)
		w.getById('change_inst').connect('on_press', self.open_choose_instrument)
		for i in range(12):
			w.getById('key_%s' % i).connect('on_press', curry(self.change_key, i))
		for i in ('Major', 'Pentatonic Major', 'Blues Major', 'Minor', 'Melodic Minor', 'Harmonic Minor', 'Pentatonic Minor', 'Blues Minor'):
			w.getById('scale_%s' % i).connect('on_press', curry(self.change_scale, i))
		
	
	
	def change_track(self, track, *largs):
		self.current_track = self.tracks[track] 
	
	def reset(self, *largs):
		self.currentrow = 0;
		
		for track in self.tracks:
			for i in range(self.gridy ):
				for j in range(self.gridx ):
					track.grid[j][i] = 0


	def on_touch_down(self, touch):
		
		#other widgets
		if super(Sequencer, self).on_touch_down(touch):
			return True
		
		#main matrix
		for x in range(self.gridx):
			#find x pad
			if (touch.x >= (2+x)*self.stepx) and (touch.x <= (2.8+x)*self.stepx):
				for y in range(self.gridy):
					#find y pad
					if (touch.y >= (2+y)*self.stepy) and (touch.y <= (2.8+y)*self.stepy):
						self.current_track.grid[x][y] = 1 - self.current_track.grid[x][y]
						return 1
		#pause mute solo
		if(touch.y >= 18.1*self.stepy and touch.y <= 19.1*self.stepy):
			if(touch.x >= 2*self.stepx and touch.x <= 2.8*self.stepx):
				self.toggle_pause()
			elif(touch.x >= 3*self.stepx and touch.x <= 3.8*self.stepx):
				self.toggle_mute()
			elif(touch.x >= 4*self.stepx and touch.x <= 4.8*self.stepx):
				self.toggle_solo()
		#track
		if(touch.y >= 18.2*self.stepy and touch.y <= 19*self.stepy):
			if(touch.x >= 5*self.stepx and touch.x <= 6.8*self.stepx):
				self.change_track(0)
			elif(touch.x >= 7*self.stepx and touch.x <= 8.8*self.stepx):
				self.change_track(1)
			elif(touch.x >= 9*self.stepx and touch.x <= 10.8*self.stepx):
				self.change_track(2)
			elif(touch.x >= 11*self.stepx and touch.x <= 12.8*self.stepx):
				self.change_track(3)
			elif(touch.x >= 13*self.stepx and touch.x <= 14.8*self.stepx):
				self.change_track(4)
		
		return 0
	
	
	def play(self,dt):
		#we move
		if self.currentrow < self.gridx - 1:
			self.currentrow += 1
		else:
			self.currentrow = 0
		
		#calculate timestamp & latency
		now = time.time()
		delta = -now + self.ts_save +60.0/self.bpm
		self.master +=1
		#if self.master == 20:
		#	exit(1)
		'''print "master %.3f now %.3f measured period %.3f delta %.3f played at %.3f" % (
			self.master*60.0/self.bpm,
			now-self.orig, 
			now - self.ts_save, 
			delta, 
			now-self.orig+delta)'''
		self.ts_save = now + delta
		
		#for each track
		for track in self.tracks:
			#first stop the preceding notes
			for i in range(self.gridy ):
				if self.currentrow > 0:
					prec = self.currentrow -1
				else:
					prec = self.gridx-1
				if track.grid[prec][i] == 1:
					#self.midi_out.note_off(track.notes[i],0,track.channel)
					self.midi_out.write([[[0x80+track.channel,track.notes[i],0],pygame.midi.time()+(delta+self.latency)*1000]])
			
			#we play
			for i in range(self.gridy ):
				if track.grid[self.currentrow][i] == 1 and not track.muted:
					#self.midi_out.note_on(track.notes[i],127,track.channel)
					self.midi_out.write([[[0x90+track.channel,track.notes[i],127],pygame.midi.time()+(delta+self.latency)*1000]])
		
		getClock().schedule_once(self.play, 60.0/self.bpm+delta)
		
	def draw(self):
		
		w = self.get_parent_window()
		
		self.stepx = w.width / (self.gridx + 4)
		self.stepy = w.height / (self.gridy + 4)
		
		#background
		set_color(0.01,0.01,0.01, 1)
		drawRoundedRectangle(
			pos = (self.stepx, 1.5*self.stepy),
			size = (17.2*self.stepx, 18*self.stepy),
			radius = 10
		)
		
		#buttons
		
		#pause
		if(self.paused):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawCircle(pos=(2.4*self.stepx, 18.6*self.stepy), radius=0.4*self.stepx)
		drawLabel(label="pause", pos=(2.4*self.stepx, 18.6*self.stepy))
		
		#mute
		if(self.current_track.muted):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawCircle(pos=(3.4*self.stepx, 18.6*self.stepy), radius=0.4*self.stepx)
		drawLabel(label="mute", pos=(3.4*self.stepx, 18.6*self.stepy))
		
		#solo
		if(self.current_track.solo):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawCircle(pos=(4.4*self.stepx, 18.6*self.stepy), radius=0.4*self.stepx)
		drawLabel(label="solo", pos=(4.4*self.stepx, 18.6*self.stepy))
		
		
		#Lead 1
		if(self.current_track.name == 'Lead 1'):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawRoundedRectangle(
			pos = ( 5*self.stepx, 18.2*self.stepy ),
		    size = ( 1.8*self.stepx, 0.8*self.stepy),
			radius = 5
		)
		drawLabel(label="Lead 1", pos=(5.9*self.stepx, 18.6*self.stepy))
		
		#Lead 2
		if(self.current_track.name == 'Lead 2'):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawRoundedRectangle(
			pos = ( 7*self.stepx, 18.2*self.stepy ),
		    size = ( 1.8*self.stepx, 0.8*self.stepy),
			radius = 5
		)
		drawLabel(label="Lead 2", pos=(7.9*self.stepx, 18.6*self.stepy))
		
		#Lead 3
		if(self.current_track.name == 'Lead 3'):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawRoundedRectangle(
			pos = ( 9*self.stepx, 18.2*self.stepy ),
		    size = ( 1.8*self.stepx, 0.8*self.stepy),
			radius = 5
		)
		drawLabel(label="Lead 3", pos=(9.9*self.stepx, 18.6*self.stepy))
		
		#bass
		if(self.current_track.name == 'Bass'):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawRoundedRectangle(
			pos = ( 11*self.stepx, 18.2*self.stepy ),
		    size = ( 1.8*self.stepx, 0.8*self.stepy),
			radius = 5
		)
		drawLabel(label="Bass", pos=(11.9*self.stepx, 18.6*self.stepy))
		
		#drum
		if(self.current_track.name == 'Drum'):
			set_color(0.53,0.83,0.28, 1)
		else:
			set_color(0.83,0.87,0.90, 1)
		drawRoundedRectangle(
			pos = ( 13*self.stepx, 18.2*self.stepy ),
		    size = ( 1.8*self.stepx, 0.8*self.stepy),
			radius = 5
		)
		drawLabel(label="Drum", pos=(13.9*self.stepx, 18.6*self.stepy))
		
		#draw pads
		for x in range(self.gridx):
			for y in range(self.gridy):
				if self.current_track.grid[x][y] == 1:
					set_color(0.53,0.83,0.28, 1) #pushed
				else:
					set_color(0.83,0.87,0.90, 1) #free
				drawRoundedRectangle( 
					pos = ( (2+x)*self.stepx, (2+y)*self.stepy ), 
				    size = ( 0.8*self.stepx, 0.8*self.stepy),
					radius = 5
				)
				#draw row played
				if(x == self.currentrow):
					set_color(.2, .2, .8, .5)
					drawRoundedRectangle(
						pos= ((2+x)*self.stepx ,(2+y)*self.stepy),
						size= (.8*self.stepx, .8*self.stepy ),
						radius = 5
					)
		#prints scale notes
		for y in range(self.gridy):
			set_color(1,1,1)
			drawLabel(self.current_track.note_names[y], pos=(1.5*self.stepx,(2.3+y)*self.stepy))
		
		#pattern number
		
	def toggle_pause(self, *largs):
		if self.paused:
			self.paused = False
		else:
			self.paused = True

	def toggle_mute(self, *largs):
		for track in self.tracks:
			track.solo = False
		if self.current_track.muted:
			self.current_track.muted = False
		else:
			self.current_track.muted = True

	def toggle_solo(self, *largs):
		if self.current_track.solo:
			for track in self.tracks:
				track.muted = False
				track.solo = False
			self.current_track.solo = False
		else:
			for track in self.tracks:
				if track.name == self.current_track.name:
					track.muted = False
					track.solo = True
				else:
					track.muted = True
					track.solo = False

	#move cells up
	def transpose_up(self, *largs):
		for x in range(self.current_track.gridx):
			save = self.current_track.grid[x][self.gridy-1]
			for y in range(self.current_track.gridy-1,0,-1):
				self.current_track.grid[x][y] = self.current_track.grid[x][y-1]
			self.current_track.grid[x][0] = save
	
	#move cells down
	def transpose_down(self, *largs):
		for x in range(self.current_track.gridx):
			save = self.current_track.grid[x][0]
			for y in range(self.current_track.gridy-1):
				self.current_track.grid[x][y] = self.current_track.grid[x][y+1]
			self.current_track.grid[x][self.current_track.gridy-1] = save

	#change tempo
	def update_bpm(self, bpm):
		self.bpm = bpm

	#change instrument window
	def open_choose_instrument(self,*largs):
		w = self.get_parent_window()
		m = MTModalWindow()
		a = MTAnchorLayout(size=w.size)
		k = MTKineticList(size=(400, 500), searchable=False,
						  deletable=False)

		def choose_instrument(item, *largs):
			w.remove_widget(m)
			self.change_instrument(*largs)

		for x in instruments:
			item = MTKineticItem(label=x, size=(400, 25))
			item.connect('on_press', curry(choose_instrument, item, x))
			k.add_widget(item)
		a.add_widget(k)
		m.add_widget(a)
		w.add_widget(m)
		



		
		
	

def pymt_plugin_activate(w, ctx):
	ctx.c = Sequencer()
	w.add_widget(ctx.c)
	
def pymt_plugin_deactivate(w, ctx):
	w.remove_widget(ctx.c)

if __name__ == '__main__':
	w = MTWindow( )
	ctx = MTContext()
	pymt_plugin_activate(w, ctx)
	runTouchApp()
	pymt_plugin_deactivate(w, ctx)
