from pymt import *

class MTMidiArpeggiator(MTDragable):
	def __init__(self, **kwargs):
		super(MTMidiArpeggiator, self).__init__(**kwargs)
		
		self.output = kwargs['output']
		
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
			if(self.index == 0):
				self.output.dispatch_event('note_on', self.note)
				self.last_note = self.note
			else:	
				self.output.dispatch_event('note_on', self.note+12)
				self.last_note = self.note+12
			self.index = 1 - self.index

	def draw(self):
		#background
		set_color(0.6,0.6,0.6, 1)
		drawRoundedRectangle(
			pos = self.pos,
			size = self.size,
			radius = 10
		)



