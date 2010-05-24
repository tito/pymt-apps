from pymt import *
from slideitems import *
from euclid import Matrix4

class ViewBookMark:
    def __init__(self, transform, **kwargs):
        self.view_transform = transform
        self.screenshot = Image(pyglet.image.get_buffer_manager().get_color_buffer().get_texture())
        self.updated = False

        
class BookmarkBar(MTBoxLayout):

    def __init__(self, **kwargs):
        kwargs.setdefault('spacing',2)
        kwargs.setdefault('padding',4)
        super(BookmarkBar, self).__init__(**kwargs)
        self.bookmarks_buttons = {}

    def add_bookmark(self, bookmark):
        bookmark_btn = MTImageButton(image=bookmark.screenshot, scale=0.1)
        @bookmark_btn.event
        def on_release(touch):
            self.parent.parent.goto_view(bookmark)

        self.bookmarks_buttons[bookmark] = bookmark_btn
        self.add_widget(bookmark_btn)

        
        self.do_layout()
            
    def update_screenshot(self, bookmark):
        bookmark.screenshot = Image(pyglet.image.get_buffer_manager().get_color_buffer().get_texture())
        self.bookmarks_buttons[bookmark].image = bookmark.screenshot
        
    def draw(self):
        drawRectangle(pos=self.pos, size=(1366,80))
        
        

class AddItemMenu(MTBoxLayout):
    def __init__(self, **kwargs):
        super(AddItemMenu, self).__init__(**kwargs)
        self.add_item_type('text', SlideText)
        self.add_item_type('image', SlideImage)
        self.add_item_type('video', SlideVideo)
        self.add_item_type('graph', SlideTracer)
        
    def add_item_type(self, name, type_factory):
        create_btn = MTButton(label=name, size=(78,78))
        @create_btn.event
        def on_press(touch):
            touch.userdata['new_item'] = type_factory
            touch.grab(self)
        self.add_widget(create_btn)

    def on_touch_up(self, touch):
        if self in touch.grab_list and (not self.collide_point(*touch.pos)):
            new_item = touch.userdata['new_item']()
            mat = Matrix4()
            mat[:] = self.parent.parent.canvas.transform_mat
            mat = mat.inverse()
            inv_mat = (GLfloat * 16)()
            for i in range(16):
                inv_mat[i] = mat[i]
            
            with gx_matrix_identity:
                glMultMatrixf(inv_mat)
                glTranslated(touch.x - new_item.width/2, touch.y - new_item.height/2, 0)
                glGetFloatv(GL_MODELVIEW_MATRIX, new_item.transform_mat) 
                
            self.parent.parent.canvas.add_widget(new_item)
            touch.ungrab(self)
                
    def draw(self):
        set_color(*self.style['bg-color'])
        drawRectangle(pos=self.pos, size=(1366,80))
        for touch in getAvailableTouchs():
            if not self in touch.grab_list:
                continue
            with gx_matrix:
                glTranslated(touch.x, touch.y, 0)
                touch.userdata['new_item'].draw_drag_icon()
        
class WorkModeController(MTBoxLayout):
    def __init__(self, **kwargs):
        super(WorkModeController, self).__init__(**kwargs)
        self.add_mode('edit')
        self.add_mode('layout')
        self.add_mode('live')

    def add_mode(self, mode_name):
        btn = MTButton(label=mode_name , size=(80,80) )
        @btn.event
        def on_release(touch):
            presentation.edit_mode = mode_name
            
        self.add_widget(btn)
           



            