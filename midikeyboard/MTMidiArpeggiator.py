from pymt import *

MIDI_ARPEGGIATOR_SEQ = [
	{ 'name': 'octaver', 'sequence': [ 0, 12 ] },
	{ 'name': 'third',   'sequence': [ 0, 4 ] },
	{ 'name': 'fifth',   'sequence': [ 0, 7 ] },
	{ 'name': 'major',   'sequence': [ 0, 4, 7 ] },
	{ 'name': 'minor',   'sequence': [ 0, 3, 7 ] },
]

class MTMidiArpeggiator(MTDragable):
	def __init__(self, **kwargs):
		super(MTMidiArpeggiator, self).__init__(**kwargs)
		
		kwargs.setdefault('sequence', 0)
		
		self.output = kwargs['output']
		self.sequence = kwargs['sequence']
		
		self.go = False
		self.last_note = -1
		self.index = 0
		
		self.register_event_type('note_on')
		self.register_event_type('note_off')
		
		b = MTButton(label='Arpeggiator1')
		self.add_widget(b)
		
		getClock().schedule_interval(self.play, 60.0/300.0)
		
	
	def note_on(self, note):
		self.note = note
		self.go = True
	
	def note_off(self, note):
		self.go = False
		self.index == 0

	def play(self, dt):
		#end of the preceding sequence note
		if self.last_note > 0:
			self.output.dispatch_event('note_off', self.last_note)
		
		if(self.go):
			s = MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence'][self.index]
			if self.index < len(MIDI_ARPEGGIATOR_SEQ[self.sequence]['sequence']) -1:
				self.index += 1
			else:
				self.index = 0
			
			self.output.dispatch_event('note_on', self.note+s)
			self.last_note = self.note+s
			

	def draw(self):
		#background
		set_color(0.6,0.6,0.6, 1)
		drawRoundedRectangle(
			pos = self.pos,
			size = self.size,
			radius = 10
		)



