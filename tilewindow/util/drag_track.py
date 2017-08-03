"""
drag_track
~~~~~~~~~~

Simple tracking of a "mouse drag" initiated inside a widget.
"""

class DragTrack():
    """Captured mouse events in the passed `widget` and when the user clicks
    and holds the mouse button, tracks how far they have dragged the mouse from
    the original start position.
    
    Change the attribute :attr:`callback` to recieve notifications.  The
    callback should have the signature `callback(dx, dy, new)` where `(dx,dy)`
    is how far the mouse has moved, and `new` is `True` if and only if the user
    has just clicked the mouse (i.e. this is a new event).

    Set the (optional) attribute :attr:`release_callback` to recieve
    notifications of when the user releases the mouse button.  Should have the
    signature `release_callback()`.
    
    Alternatively, subclass and override `moved` and `released`.
    
    We completely the steal the "<Motion>", "<Button>" and "<ButtonRelease>"
    bindings.  Change the `additive` parameter to `add` bindings instead.
    
    More sophisticated applications may wish to handle some clicking events
    themselves.  To do this, subclass and override ?????????????????
    
    :param widget: The `tk` widget to track mouse dragging in.
    :param button: Which mouse button to track (1==left, the default; 2==right)
    :param additive: Set to `True` to add additional bindings instead of
      replacing existing bindings.
    """
    def __init__(self, widget, button=1, additive=False):
        self.callback = None
        self.release_callback = None
        self._drag_track_start = None
        self._drag_track_button = button
        if button == 1:
            self._drag_track_button_mask = 256
        elif button == 2:
            self._drag_track_button_mask = 1024
        else:
            raise ValueError("Cannot bind to button {}".format(button))
        widget.bind("<Motion>", self._motion, add=additive)
        widget.bind("<Button>", self._down, add=additive)
        widget.bind("<ButtonRelease>", self._up, add=additive)

    def moved(self, dx, dy, new):
        """Called when the user has clicked the mouse and is dragging.
        
        By default we delegate to `self.callback` if this is not `None`.
        
        :param dx: The amount of horizontal movement since dragging started.
        :param dy: The amount of vertical movement since dragging started.
        :param new: Is this is the first click (i.e. this is called with `True`
          at the start of the dragging, and then called repeatedly with `False`
          while dragging continues).
        """
        if self.callback is not None:
            self.callback(dx, dy, new)

    def released(self):
        """Called at the end of a dragging event.
        
        By default we delegate to `self.release_callback` if this is not
        `None`.
        """
        if self.release_callback is not None:
            self.release_callback()

    def notify(self, event, what):
        """Notify of an event happening.  This is a hook for (conditionally)
        handling events.
        
        :param event: The `tkinter` `event` object.
        :param what: One of `down`, `up` and `motion` for, respectively, the
          user pressing (any) mouse button, releasing the button, and moving.
          
        :return: `True` if you have handled the event yourself.  Default is to
          always return `False`.
        """
        return False

    def _down(self, event):
        if self.notify(event, "down"):
            return
        if event.num == self._drag_track_button:
            self._drag_track_start = (event.x, event.y)
            self.moved(0, 0, True)

    def _up(self, event):
        if self.notify(event, "up"):
            return
        self._drag_track_start = None
        self.released()

    def _motion(self, event):
        if self.notify(event, "motion"):
            return
        if self._drag_track_start is None:
            return
        if not (event.state & self._drag_track_button_mask):
            self._up(None)
        self.moved(event.x - self._drag_track_start[0], event.y - self._drag_track_start[1], False)
