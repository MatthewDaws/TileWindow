"""
image
~~~~~

A widget, based on a `tk.canvas` and `image`, which displays a large image and
allows the user to drag the image.
"""

import tkinter as tk
import tkinter.ttk as ttk
from .util import util
from .util import scrollbars
from tilewindow.util.drag_track import DragTrack
import PIL.ImageTk, PIL.Image

class Image(tk.Canvas):
    """A subclass of :class:`tkinter.Canvas` which supports displaying an image
    and allowing the user the scroll it by clicking and dragging.

    Supports zooming, using the `pillow` library.

    Either allows free dragging of the image (designed mainly for subclasses
    which will dynamically generate content) or clampling the view to the
    image.  In "clamp" mode, if the view is larger than the image, then allows
    "anchoring".  Has overriden scroll-bar support (only for "clamp" mode).

    You can set the :attr:`mouse_handler` attribute to have some control over
    how mouse input is handled.

    (We intercept the standard `tkinter` calls; you can set the
    `xscrollcommand` either in the constructor, with
    `widtget["xscrollcommand"] = ...` with `widget.config(xscrollcommand=...)`
    or with `widget.configure(xscrollcommand=...)`.  However, using `cget` etc.
    to retrieve the current settings will not work.)

    By default, we set the border width and highlightwidth to 0.  This is
    important to allow us to correctly calculate the size of the viewable area.

    :param parent: The `tkinter` widget which is the parent
    :param free: Set to `True` to allow dragging the image anywhere; set to
      `False` to clamp the view to the image, and to align the image according
      to :attr:`anchor` if the view is larger than the image.
    :param anchor: Set to one of `tk.N`, `tk.NW` etc. or `tk.CENTER` to be
      where the image appears when the canvas is larger than the image.
    :param **kwargs: Other parameters to be passed to the `tk.Canvas`
      constructor.
    """
    def __init__(self, parent, free=False, anchor=tk.CENTER, **kwargs):
        super().__init__(parent, **self._init_adjust_kwargs(kwargs))
        self._image_id = self.create_image(0, 0, anchor=tk.NW)
        self.bind("<Configure>", self._conf)
        self._photo = None
        self._image = None
        self._current_location = (0, 0)
        self._needed_width, self._needed_height = 0, 0
        self.anchor = anchor
        self.free = free
        self._tracker = self._OurTracker(self)

    @property
    def size(self):
        """The size of the view.
        
        :return: `(width, height)`
        """
        return self._needed_width, self._needed_height

    def set_image(self, image, allow_zoom=False, location=None):
        """Set the displayed image.  Does not change the view if this is
        possible, given the new image size.

        :param image: A :class:`PIL.Image` instance.
        :param allow_zoom: Set to true to allowing zooming.  Keeps a reference
          to the image.
        :param location: If not `None` then also update the current view
          position.
        """
        self.set_photo(PIL.ImageTk.PhotoImage(image), location)
        if allow_zoom:
            self._image = image
        else:
            self._image = None

    def set_photo(self, photo, location=None):
        """Set the displayed image.  Does not change the view if this is
        possible, given the new image size.  We capture a reference to the
        `photo` to avoid it being garbage collected.

        :param photo: A :class:`PhotoImage` or :class:`PIL.ImageTk` instance.
        :param location: If not `None` then also update the current view
          position.
        """
        self._photo = photo
        self.itemconfigure(self._image_id, image=self._photo)
        if location is not None:
            dx = location[0] - self._current_location[0]
            dy = location[1] - self._current_location[1]
            self._tracker.add_to_bias(dx, dy)
            self._current_location = location
        self._redraw()

    @property
    def zoom(self):
        """The current zoom level.  Zooming is only supported for images."""
        return self._zoom

    @zoom.setter
    def zoom(self, z):
        if self._image is None:
            raise ValueError("No stored image to zoom from")
        self._zoom = float(z)
        if abs(self._zoom - 1) < 1e-5:
            self.set_photo(PIL.ImageTk.PhotoImage(self._image))
        else:
            w = int(self._image.width * self.zoom)
            h = int(self._image.height * self.zoom)
            image = self._image.resize((w,h), PIL.Image.ANTIALIAS)
            self.set_photo(PIL.ImageTk.PhotoImage(image))

    @property
    def anchor(self):
        """Set to one of `tk.N`, `tk.NW` etc. or `tk.CENTER` to be where the
        image appears when the canvas is larger than the image."""
        return self._image_anchor

    @anchor.setter
    def anchor(self, v):
        if v not in {tk.CENTER, tk.N, tk.NE, tk.E, tk.SE, tk.S, tk.SW, tk.W, tk.NW}:
            raise ValueError()
        self._image_anchor = v
        self._redraw()

    @property
    def free(self):
        """Set to `True` to allow dragging the image anywhere; set to `False`
        to clamp the view to the image, and to align the image according to
        :attr:`anchor` if the view is larger than the image."""
        return self._free

    @free.setter
    def free(self, v):
        self._free = bool(v)
        self._redraw()

    def move_to(self, x, y):
        """More the image so that the location `(x, y)` is the upper-left
        corner of the canvas.  If :attr:`free` is `False`, then the actual
        location of the image will be adjusted given the value of
        :attr:`anchor`.
        """
        if self._photo is None or self._needed_width <= 0 or self._needed_height <= 0:
            return
        if self._free:
            self._current_location = (x, y)
            self.scan_dragto(-x, -y, gain=1)
            xx = self._needed_width - self._photo.width() + x
            yy = self._needed_height - self._photo.height() + y
            self.notify_of_gap(-x, -y, xx, yy)
        else:
            self._move_to_adjusted(x, y)

    def _move_to_adjusted(self, x, y):
        x, y = max(0, int(x)), max(0, int(y))
        extra_x = int(self._photo.width() - self._needed_width)
        if extra_x < 0:
            x = 0
        else:
            x = min(x, extra_x)
        extra_y = int(self._photo.height() - self._needed_height)
        if extra_y < 0:
            y = 0
        else:
            y = min(y, extra_y)
        self._current_location = (x, y)
        
        xx, yy = x, y
        if extra_x < 0:
            if self._image_anchor in {tk.NW, tk.W, tk.SW}:
                xx = 0
            elif self._image_anchor in {tk.NE, tk.E, tk.SE}:
                xx = extra_x
            else:
                xx = int(extra_x // 2)
        if extra_y < 0:
            if self._image_anchor in {tk.NW, tk.N, tk.NE}:
                yy = 0
            elif self._image_anchor in {tk.SE, tk.S, tk.SW}:
                yy = extra_y
            else:
                yy = int(extra_y // 2)
        
        # Where the _canvas_ will be moved to; the image is always at (0, 0)
        self.scan_dragto(-xx, -yy, gain=1)
        self.notify_of_gap(-xx, -yy, xx - extra_x, yy - extra_y)
        xt = self._photo.width()
        self._update_xscroll(max(0, xx / xt), min(1, 1 - (extra_x - xx) / xt))
        yt = self._photo.height()
        self._update_yscroll(max(0, yy / yt), min(1, 1 - (extra_y - yy) / yt))

    @property
    def current_location(self):
        """The current image coordinates `(x,y)` which form the upper-left
        corner of the canvas.  Does not take account of :attr:`anchor`, so, for
        example, if the image is smaller than the canvas, will return `(0,0)`
        while the image may well actually be centred on the canvas.
        """
        return self._current_location

    def notify_of_gap(self, left, top, right, bottom):
        """Called to notify that the displayed window is now larger than the
        image.  Each number specifies the "extra" number of pixels we need.
        Sub-classes should override this.

        :param left: 0 indicates the image is at the hard left of the window.
          `>0` indicates that many extra pixels are needed, and `<0` indicates
          that no extra pixels are needed.
        :param top: Same for the top
        :param right: Same for the right
        :param bottom: Same for the bottom
        """
        pass

    @property
    def mouse_handler(self):
        """The currently used instance of :class:`MouseHandler` to
        conditionally handle mouse events.  Or `None`."""
        return self._tracker.mouse_handler

    @mouse_handler.setter
    def mouse_handler(self, v):
        self._tracker.mouse_handler = v

    def make_scroll_bars(self, parent):
        """Helper method to build horizontal and vertical scroll bars linked
        correctly to the widget.  Uses our :class:`Scrollbar` which is a tiny
        extension of the :class:`tkinter.ttk.Scrollbar` widget.

        :param parent: The `tkinter` widget to be the parent to the bars.

        :return: `(xscrollbar, yscrollbar)`
        """
        xscroll = scrollbars.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.xview)
        self["xscrollcommand"] = xscroll.set
        yscroll = scrollbars.Scrollbar(parent, orient=tk.VERTICAL, command=self.yview)
        self["yscrollcommand"] = yscroll.set
        return xscroll, yscroll

    def _xy_view(self, how, args, start, end, total):
        """Private method to deal with scroll commands.
          - A "units" scroll moves 2% of the width/height.
          - A "pages" scroll moves a whole window in width/height
        """
        if how == tk.MOVETO:
            new_start = float(args[0])
            diff = (new_start - start) * total
        elif how == tk.SCROLL:
            num, what = int(args[0]), args[1]
            if what == "units":
                diff = num * total // 50
            elif what == "pages":
                diff = int(num * (end - start) * total)
            else:
                raise ValueError("Unknown 'what' : '{}'".format(what))
        else:
            raise ValueError("Unknown 'how': '{}'".format(how))
        return diff        

    def xview(self, how, *args):
        """Our handling of the standard `xview`."""
        diff = self._xy_view(how, args, self._xstart, self._xend, self._photo.width())
        x, y = self.current_location
        self._move_to_adjusted(x + diff, y)

    def yview(self, how, *args):
        """Our handling of the standard `yview`."""
        diff = self._xy_view(how, args, self._ystart, self._yend, self._photo.height())
        x, y = self.current_location
        self._move_to_adjusted(x, y + diff)

    def _init_adjust_kwargs(self, kwargs):
        kwargs_copy = self._capture_scroll_commands(kwargs)
        if "borderwidth" not in kwargs_copy:
            kwargs_copy["borderwidth"] = 0
        if "highlightthickness" not in kwargs_copy:
            kwargs_copy["highlightthickness"] = 0
        return kwargs_copy

    def _capture_scroll_commands(self, kwargs):
        kwargs_copy = dict(kwargs)
        for p in ["x", "y"]:
            key = p + "scrollcommand"
            if key in kwargs_copy:
                self[key] = kwargs_copy[key]
                del kwargs_copy[key]
        return kwargs_copy

    def config(self, cnf=None, **kwargs):
        kwcopy = dict(kwargs)
        kwcopy.update(cnf)
        kwcopy = self._capture_scroll_commands(kwcopy)
        if len(kwcopy) > 0:
            super().config(**kwcopy)

    def configure(self, cnf=None, **kwargs):
        self.config(cnf, **kwargs)

    def __setitem__(self, key, value):
        if key == "xscrollcommand":
            self._xscroll_command = value
        elif key == "yscrollcommand":
            self._yscroll_command = value
        else:
            super().__setitem__(key, value)

    def _update_xscroll(self, start, end):
        """If we have set the `xscrollcommand` then call it."""
        if hasattr(self, "_xscroll_command") and self._xscroll_command is not None:
            self._xstart, self._xend = start, end
            self._xscroll_command(start, end)

    def _update_yscroll(self, start, end):
        """If we have set the `yscrollcommand` then call it."""
        if hasattr(self, "_yscroll_command") and self._yscroll_command is not None:
            self._ystart, self._yend = start, end
            self._yscroll_command(start, end)

    def _conf(self, event):
        """Captures the widget being resized."""
        self._needed_width = self.winfo_width()
        self._needed_height = self.winfo_height()
        self._redraw()

    def _redraw(self):
        self.move_to(*self.current_location)

    class _OurTracker(DragTrack):
        """Handle mouse movement messages."""
        def __init__(self, canvas):
            super().__init__(canvas)
            self._parent = canvas
            self._bias = 0, 0
            self.mouse_handler = None

        def notify(self, event, what):
            if self.mouse_handler is None:
                return False
            if what == "motion":
                self._parent.after_idle(lambda x=event.x, y=event.y : self._eventual_notify(x, y))
            return self.mouse_handler.handle(event, what)

        def _eventual_notify(self, x, y):
            x += self._parent.current_location[0]
            y += self._parent.current_location[1]
            self.mouse_handler.notify(x, y)

        def add_to_bias(self, x, y):
            self._bias = self._bias[0] + x, self._bias[1] + y

        def moved(self, dx, dy, new):
            if new:
                self._sx, self._sy = self._parent.current_location
                self._bias = 0, 0
            x, y = self._sx - dx, self._sy - dy
            x += self._bias[0]
            y += self._bias[1]
            self._parent.move_to(x, y)


class MouseHandler():
    """Interface for handling mouse events.  By default, we capture all mouse
    events in the canvas and deal with them ourselves.  Some typical use cases
    for user handling:
    
    - Change the pointer when the mouse button is being held down, to give a
      visual indication of dragging happening.
    - Intercept and handle for ourselves certain click events: e.g. the user
      clicking on a widget displayed above the image.
    - The user clicks with the right mouse button or moves the mouse wheel.

    Our current way of intercepting the motion _before_ dealing with dragging
    means that during dragging, the reported position can get (by small amount)
    out of sync with the actual position...
    """
    def handle(self, event, what):
        """Notify of an event happening.  This is a hook for (conditionally)
        handling events at the level of `tkinter`.
        
        :param event: The `tkinter` `event` object.
        :param what: One of `down`, `up` and `motion` for, respectively, the
          user pressing (any) mouse button, releasing the button, and moving.
          
        :return: `True` if you have handled the event yourself.  Default is to
          always return `False`.
        """
        return False

    def notify(self, x, y):
        """The mouse is currently over these coordinates in "image space".
        This is purely a "notification", but the `(x,y)` coordinates will be
        pre-processed to be "correct"."""
        pass


class MouseHandlerChain(MouseHandler):
    """A version :class:`MouseHandler` which has a "delegate" and by defaults
    forwards to that delegate.  A useful to subclass to generate a "chain" of
    notifications.

    :param delegate: The next instance of :class:`MouseHandler` to call.
    """
    def __init__(self, delegate=None):
        self._delegate = delegate

    def handle(self, event, what):
        if self._delegate is not None:
            return self._delegate.handle(event, what)
        return False

    def notify(self, x, y):
        if self._delegate is not None:
            return self._delegate.notify(x, y)


class MouseCursorHandler(MouseHandlerChain):
    """Change the cursor when the user drags.
    
    :param canvas: The :class:`Image` instance (or other `tkinter` widget) to
      change the cursor of.
    :param delegate: Another :class:`MouseHandler` to delegate to, or `None`
    :param cursor: The string name of the `tkinter` cursor.
    """
    def __init__(self, canvas, delegate=None, cursor="hand2"):
        super().__init__(delegate)
        self._canvas = canvas
        self._old = ""
        self._cursor = cursor

    def handle(self, event, what):
        if what == "down":
            self._old = self._canvas["cursor"]
            self._canvas["cursor"] = self._cursor
        elif what == "up":
            self._canvas["cursor"] = self._old
        return super().handle(event, what)

    def notify(self, x, y):
        super().notify(x, y)
