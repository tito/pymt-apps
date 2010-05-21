from pymt import *
import random

MIDI_ARPEGGIATOR_SEQ = [
	{ 'name': 'octaver', 'sequence': [ 0, 12 ] },
	{ 'name': 'third',   'sequence': [ 0, 4 ] },
	{ 'name': 'fifth',   'sequence': [ 0, 7 ] },
	{ 'name': 'major',   'sequence': [ 0, 4, 7 ] },
	{ 'name': 'minor',   'sequence': [ 0, 3, 7 ] },
	{ 'name': 'popcorn', 'sequence': [ 0, -2, 0, -5, -9, -5, -12, 's' ] }
]

class MTMidiArpeggiator(MTScatterWidget):
	def __init__(self, **kwargs):
		super(MTMidiArpeggiator, self).__init__(**kwargs)
		
		self.do_scale = False
		self.do_rotation = False
		
		kwargs.setdefault('sequence', 0)
		kwargs.setdefault('random', False)
		
		self.output = kwargs['output']
		self.sequence = kwargs['sequence']
		self.random = kwargs['random']
		
		self.go = False
		self.last_note = -1
		self.index = 0
		
		self.register_event_type('note_on')
		self.register_event_type('note_off')
		self.register_event_type('on_check')
		
		l = MTBoxLayout(size=self.size, pos=(10,10))
		
		self.button = MTButton(label=MIDI_ARPEGGIATOR_SEQ[self.sequence]['name'], size=(120,80))
		self.button.connect('on_press', self.open_choose_arpeggiator)

		self.buttonr = MTToggleButton(label='random', size=(60,80))
		self.buttonr.connect('on_press', self.toggle_random)
		
		l.add_widget(self.button)
		l.add_widget(self.buttonr)
		self.add_widget(l)
		
		getClock().schedule_interval(self.play, 60.0/300.0)
		
	def toggle_random(self,*largs):
		print "random"
		self.random = 1 - self.random
		if self.random:
			self.buttonr.state = 'down'
		
		
	def note_on(self, note):
		self.note = note
		self.go = True
	
	def note_off(self, note):
		self.go = False
		self.index == 0

	def play(self, dt):
		#end of the preceding sequence note
		if self.last_note > 0 and self.last_note != 's':
			self.output.dispatch_event('note_off', self.last_note)
		
		if(self.go):
			if self.random:
				s = MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence'][random.randint(0,len(MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence'])-1)]
			else:
				s = MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence'][self.index]
				if self.index < len(MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence']) -1:
					self.index += 1
				else:
					self.index = 0
			
			if s != 's':
				self.output.dispatch_event('note_on', self.note+s)
				self.last_note = self.note+s
			else:
				self.last_note = 's'
			

	def draw(self):
		#background
		set_color(0.6,0.6,0.6, 1)
		drawRoundedRectangle(
			pos = (0,0),
			size = self.size,
			radius = 10
		)

	def open_choose_arpeggiator(self,*largs):
		w = self.get_parent_window()
		m = MTModalWindow()
		a = MTAnchorLayout(size=w.size)
		k = MTKineticList(size=(400, 500), searchable=False,
						  deletable=False)

		def choose_instrument(num, name, *largs):
			w.remove_widget(m)
			self.sequence = num
			self.button.label = name
			self.index = 0

		num = 0
		for x in MIDI_ARPEGGIATOR_SEQ:
			item = MTKineticItem(label=x['name'], size=(400, 50))
			item.connect('on_press', curry(choose_instrument, num, x['name']))
			k.add_widget(item)
			num += 1
		a.add_widget(k)
		m.add_widget(a)
		w.add_widget(m)

