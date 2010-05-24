from pymt import *
from pyglet.gl import *

from controlls import *
import presentation


class Slide(MTWidget):
    def __init__(self, **kwargs):
        self.slide_show = kwargs.get('slide_show')
        super(Slide, self).__init__(**kwargs)



class ImageSlide(Slide):
    def __init__(self, img, **kwargs):
        super(ImageSlide, self).__init__(**kwargs)
        self.image = Image(img)

    def draw(self):
        with gx_matrix:
            glScaled(self.parent.width/float(self.image.width), self.parent.height/float(self.image.height), 1.0)
            self.image.draw()
            
    def on_touch_up(self, touch):
        self.parent.next_slide()




import euclid

class ScatterSlide(Slide):
    def __init__(self, **kwargs):
        
        super(ScatterSlide, self).__init__(**kwargs)
        
        self.canvas = ScatterSlideCanvas()
        canvas_layer = MTWidget()
        canvas_layer.add_widget(self.canvas)
        super(ScatterSlide, self).add_widget(canvas_layer)
        
        self.controlls = MTWidget()
        super(ScatterSlide, self).add_widget(self.controlls)
        
        #self.next_btn = MTButton(label="next slide", pos=(getWindowWidth()-60,0), size=(60,30))
        #self.next_btn.push_handlers(on_press=presentation.root.next_slide)
        #self.controlls.add_widget(self.next_btn)
        
        self.save_view_btn = MTButton(label="save view", pos=(0,768-80), size=(80,80))
        self.save_view_btn.push_handlers(on_press=self.save_view)
        self.controlls.add_widget(self.save_view_btn)
        
        self.bookmarks = BookmarkBar(pos=(82,768-80) )
        self.controlls.add_widget(self.bookmarks)
        
        self.add_menu = AddItemMenu()
        self.controlls.add_widget(self.add_menu)
        
        self.mode_menu = WorkModeController(pos=(1366-240,0))
        self.controlls.add_widget(self.mode_menu)

        self.current_bookmark = None
        
        self.interpolation = 0.0
        self.save_view()
        
    def add_widget(self, w, top=True):
        controller = ScatterSlideElementController()
        controller.add_widget(w)
        self.canvas.add_widget(controller)
        
    def save_view(self, touch=None):
        #self.saved_views.append()
        self.bookmarks.add_bookmark(ViewBookMark(self.capture_current_view()))
        
    def goto_view(self, bookmark):
        self.source_view = bookmark.view_transform
        self.destination_view = self.capture_current_view()
        self.current_bookmark = bookmark
        self.interpolation = 1.0
        
    def capture_current_view(self):
        scale = Vector(*self.canvas.to_parent(1,1)).distance(Vector(*self.canvas.to_parent(100,1)))
        scale *= 0.01
        pos = self.canvas.to_parent(0,0)
        mat_trans = euclid.Matrix4()
        mat_trans[:] = self.canvas.transform_mat
        mat_trans.translate(-pos[0],-pos[1],0)
        mat_trans.scale(1.0/scale, 1.0/scale, 1.0)
        return (scale, pos, euclid.Quaternion.new_rotate_matrix(mat_trans))
        
    def on_update(self):
        if self.interpolation <= 0.0:
            return
        
        i =  self.interpolation
        sx,sy = self.source_view[1]
        tx,ty = self.destination_view[1]
        dx,dy = sx+i*(tx-sx), sy+i*(ty-sy)
        mat1 = euclid.Matrix4.new_translate(dx,dy,1)
        
        src_scale = self.source_view[0]
        dst_scale = self.destination_view[0]
        scale = src_scale+ i*(dst_scale-src_scale)
        #scale = max(0.0000001,scale)
        mat2 = euclid.Matrix4.new_scale(scale,scale,1)
        
        qatern = euclid.Quaternion.new_interpolate(self.source_view[2], self.destination_view[2], i)
        mat3 = qatern.get_matrix()
         
        mat = mat1 * (mat2 * mat3) 

        for i in range(16):
            self.canvas.transform_mat[i] = mat[i]
            
        self.interpolation -= 0.01
        if self.interpolation <= 0.0 and self.current_bookmark: #now we are done
            self.bookmarks.update_screenshot(self.current_bookmark)
            self.current_bookmark = None
        

       
     
class ScatterSlideCanvas(MTScatterPlane):
    def __init__(self, **kwargs):
        super(ScatterSlideCanvas, self).__init__(**kwargs)
        
        self.grid_dl = GlDisplayList()
        with self.grid_dl:
            glColor3f(*presentation.grid_color)
            glLineWidth(1)
            for i in range(-1000,1000):
                drawLine((i*50, -50000, i*50, 50000))
                drawLine((-50000, i*50, 50000, i*50))
         
    def draw(self):
        self.grid_dl.draw()
