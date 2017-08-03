# Demos the use of drag_track in a couple of different `tkinter` widgets
#
# Things you can change:
#  - If you don't set the `scrollregion` in the `CanvasTracker` constructor
#    then you can drag the canvas indefinitely!

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow.util.util as util
from tilewindow.util.drag_track import DragTrack

import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
util.centre_window_percentage(root, 50, 50)

label_frame = ttk.LabelFrame(root, text="Label Frame", width=200, height=200)
label_frame.grid_propagate(False)
label_frame.grid(row=0, column=0)
lf_dt = DragTrack(label_frame)
label = ttk.Label(label_frame)
label.grid()

def lf_callback(dx, dy, new=False):
    label["text"] = "dx={}, dy={}, new={}".format(dx, dy, new)

def lf_release():
    label["text"] = "click here!"

lf_dt.callback = lf_callback
lf_dt.release_callback = lf_release
lf_release()

lf = ttk.LabelFrame(root, text="Canvas object")
lf.grid(row=0, column=1)
canvas = tk.Canvas(lf, borderwidth=0, highlightthickness=0)
canvas.grid(sticky=tk.NSEW)
canvas["width"] = 300
canvas["height"] = 200


class CanvasTracker(DragTrack):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.text_id = canvas.create_text(20, 20, anchor=tk.NW)
        self.released()
        self.rect_id = canvas.create_rectangle(20, 50, 120, 100, width=2, fill="green")
        self.move_rect_id = canvas.create_rectangle(150, 70, 170, 90, width=1, fill="red")
        self._grabbed = None
        canvas.config(scrollregion=(-50,-50, 350,250))
        
    def _in_rect(self, event, rect_id):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        minx, miny, maxx, maxy = self.canvas.bbox(rect_id)
        return ( minx <= x and x <= maxx and miny <= y and y <= maxy )
        
    def notify(self, event, what):
        if what == "down":
            if self._in_rect(event, self.rect_id):
                return True
            if self._in_rect(event, self.move_rect_id):
                self._grabbed = event.x - self.canvas.canvasx(event.x), event.y - self.canvas.canvasy(event.y)
        if what == "up":
            self._grabbed = None
        return False
        
    def moved(self, dx, dy, new=False):
        self.canvas.itemconfigure(self.text_id,
                text = "dx={}, dy={}, new={}".format(dx, dy, new))
        if self._grabbed is not None:
            # Slightly complex.  Call `canvas.xview_moveto(p)` where `p` is the
            # fraction of the entire width of the `scrollregion`.  For us, this
            # is 400.  But the canvas "window" is 300 wide, so we can only
            # actually scroll between 0 and 100 or, as fractions, 0.0 and 0.25
            #x = -self._grabbed[0] - dx
            #y = -self._grabbed[1] - dy
            #canvas.xview_moveto((x+50) / 100 * 0.25)
            #canvas.yview_moveto((y+50) / 100 * (300-200)/300)
            
            # Alternative, somewhat nicer method!
            x = dx + self._grabbed[0]
            y = dy + self._grabbed[1]
            canvas.scan_dragto(int(x), int(y), gain=1)

    def released(self):
        self.canvas.itemconfigure(self.text_id, text = "click here!")


CanvasTracker(canvas)

ttk.Label(root, text="Notice that you can click anywhere inside the 'canvas' object\n"
          + "and the tracking works.  But if you click inside the 'label frame'\n"
          + "object but on top of the text, it doesn't work.  The text is a new widget\n"
          + "which doesn't have mouse capture enabled.\n"
          + "We manually intercept clicks in the green rectangle and ignore them.\n"
          + "Click and drag the red rectangle to drag the whole canvas about."
          ).grid(row=1, column=0, columnspan=2)


root.mainloop()