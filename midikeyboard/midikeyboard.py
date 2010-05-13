# PYMT Plugin integration
IS_PYMT_PLUGIN = True
PLUGIN_TITLE = 'Midi Keyboard'
PLUGIN_AUTHOR = 'Remi Pauchet'
PLUGIN_DESCRIPTION = 'Play!'


from pymt import *
from MTMidiKeyboard import *
from MTMidiInstrument import *
from MTMidiArpeggiator import *
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
		
		midi_out = pygame.midi.Output(self.device)
		#end midi init
		
		i1 = MTMidiInstrument( pos=(100,400), size=(200,100), instrument=0, channel=0, midi_out = midi_out)
		k1 = MTMidiKeyboard(   pos=(100,100), size=(300,200), output = i1)
		
		i2 = MTMidiInstrument( pos=(500,600), size=(200,100), instrument=87, channel=1, midi_out = midi_out)
		ar = MTMidiArpeggiator(pos=(500,400), size=(200,100), sequence=4, output = i2)
		k2 = MTMidiKeyboard(   pos=(500,100), size=(300,200), octave=1, output = ar)
		
		self.add_widget(k1)
		self.add_widget(k2)
		self.add_widget(i1)
		self.add_widget(i2)
		self.add_widget(ar)
	

			

			

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
