from slide import SlideItem
from untangle import GraphUI

class SlideTracer(SlideItem):
    name = 'untangle'
    def __init__(self, *largs, **kwargs):
        super(SlideTracer, self).__init__(*largs, **kwargs)
        self.size = (600,600)
        self.locked = False
        self.tracer = GraphUI(10)
        self.add_widget(self.tracer)

