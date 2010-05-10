# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Midi Keyboard'
PLUGIN_AUTHOR = 'Remi Pauchet'
PLUGIN_DESCRIPTION = 'Play!'


from pymt import *
from MTMidiKeyboard import *
import pygame.midi



class World(MTWidget):
	def __init__(self, **kwargs):
		super(World, self).__init__(**kwargs)
		
		#midi init
		pygame.midi.init()
		
		c = pygame.midi.get_count()
		print "%s midi devices found" % c
		for i in range(c):
			print "%s name: %s input: %s output: %s opened: %s" % (pygame.midi.get_device_info(i))
		self.device = pygame.midi.get_default_output_id()
		print "Default is %s" % self.device
		
		self.midi_out = pygame.midi.Output(self.device)
		self.midi_out.set_instrument(0, channel=0)		
		self.midi_out.set_instrument(24, channel=1)	

		self.piano = MTMidiKeyboard(pos=(100,100), size=(300,200), channel = 0, midiplay = self)
		self.guitar  = MTMidiKeyboard(pos=(500,100), size=(300,200), channel = 1, midiplay = self)
		
		self.add_widget(self.piano)
		self.add_widget(self.guitar)
		
		self.register_event_type('note_on')
		self.register_event_type('note_off')
	
	def note_on(self, channel, note):
		self.midi_out.note_on(note,127,channel)
	
	def note_off(self, channel, note):
		self.midi_out.note_off(note,127,channel)

			

			

def pymt_plugin_activate(w, ctx):
	ctx.c = World()
	w.add_widget(ctx.c)
	
def pymt_plugin_deactivate(w, ctx):
	w.remove_widget(ctx.c)

if __name__ == '__main__':
	w = MTWindow( )
	ctx = MTContext()
	pymt_plugin_activate(w, ctx)
	runTouchApp()
	pymt_plugin_deactivate(w, ctx)
