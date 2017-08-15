"""
tiler
~~~~~

Handles generating large / infinite images from tiles.
"""

import math as _math
import threading as _threading
import time as _time
import queue
import PIL.Image
from . import image
import logging as _logging

class TileWindow():
    """Internal class which stores details of a large or infinite image:

      - :attr:`image_bounds` which is the size of the total image.
      - :attr:`window` the currently viewed rectangle of the total image.
      - :attr:`buffer_extent` the rectangle of the total image which we have
        stored in memory.  Will always exactly align with tile width / height,
        and should contain the "window" (but may not during the update cycle).
      - :attr:`border` the number of tiles in a border we aim to keep around
        the "window" in the "buffer".

    A typical update sequence is to set :attr:`window` and then query
    :attr:`needed_buffer_extent` to find the buffer we need; if this doesn't
    match :attr:`buffer_extent` then update.

    :param tilewidth: Width of each tile
    :param tileheight: Height of each tile
    :param **kwargs: Set any properties by keyword.
    """
    def __init__(self, tilewidth, tileheight, **kwargs):
        self._tile_width = tilewidth
        self._tile_height = tileheight
        
        self.image_bounds = (None, None, None, None)
        self.window = (0, 0, self._tile_width, self._tile_height)
        self.border = 1
        self.buffer_extent = (0, 0, 0, 0)

        for key, value in kwargs.items():
            try:
                if not hasattr(self, key):
                    raise Exception()
                setattr(self, key, value)
            except:
                raise ValueError("Have no property of name '{}'".format(key))

    @property
    def image_bounds(self):
        """The bounds of the image, `(xmin, ymin, xmax, ymax)`.  Any can be
        `None` indicating no bound in that direction.  As we are dealing with
        pixels, we follow the convention that for example `(0, 0, 100, 50)`
        defines an image of width 100 and height 50.
        """
        return self._bounds

    @staticmethod
    def _int_or_none(x):
        if x is None:
            return x
        return int(x)

    @image_bounds.setter
    def image_bounds(self, v):
        try:
            v = tuple(self._int_or_none(x) for x in v)
            assert len(v) == 4
            assert v[0] is None or v[0] % self.tile_width == 0
            assert v[1] is None or v[1] % self.tile_height == 0
            assert v[2] is None or v[2] % self.tile_width == 0
            assert v[3] is None or v[3] % self.tile_height == 0
            self._bounds = v
        except:
            raise ValueError("Should be a tuple of length 4.")

    @property
    def tile_width(self):
        """Width of each tile"""
        return self._tile_width

    @property
    def tile_height(self):
        """Height of each tile"""
        return self._tile_height

    @property
    def window(self):
        """The current viewable window `(xmin, xmax, ymin, ymax)`."""
        return self._window

    @window.setter
    def window(self, v):
        try:
            v = tuple(int(x) for x in v)
            assert len(v) == 4
            self._window = v
        except:
            raise ValueError("Should be a tuple of 4 integers")

    @property
    def border(self):
        """The width of the tile "border" to maintain around the window.
        By default is `1`; set to a higher value to allow the user to scroll
        the window further without requiring new tiles, at the cost of
        increased memory usage, and the need to generate more tiles."""
        return self._border

    @border.setter
    def border(self, v):
        try:
            v = int(v)
            assert v > 0
            self._border = v
        except:
            raise ValueError("Should be an integer >= 1")

    @property
    def buffer_extent(self):
        """The rectangle bounding the "buffer": the rectangle of tiles which we
        currently have.  Takes the form `(xmin, ymin, xmax, ymax)` where these
        coordinates will be multiples of the respective tile width or height."""
        return self._buffer

    @property
    def buffer_width(self):
        """Width of the :attr:`buffer_extent`"""
        return self.buffer_extent[2] - self.buffer_extent[0]

    @property
    def buffer_height(self):
        """Height of the :attr:`buffer_extent`"""
        return self.buffer_extent[3] - self.buffer_extent[1]

    @buffer_extent.setter
    def buffer_extent(self, v):
        try:
            v = tuple(int(x) for x in v)
            assert len(v) == 4
            assert v[0] % self.tile_width == 0
            assert v[2] % self.tile_width == 0
            assert v[1] % self.tile_height == 0
            assert v[3] % self.tile_height == 0
            self._buffer = v
        except:
            raise ValueError("Should be a tuple (xmin, ymin, xmax, ymax), multiples of the tile size.")

    @property
    def needed_buffer_extent(self):
        """Given the current :attr:`window` and :attr:`border`, and taking
        account of :attr:`image_bounds`, what is the buffer we need?  Returns
        `(xmin, ymin, xmax, ymax)` as :attr:`buffer_extent`"""
        # In "tile space"
        xmin = _math.floor(self.window[0] / self.tile_width) - self.border
        ymin = _math.floor(self.window[1] / self.tile_height) - self.border
        xmax = _math.ceil(self.window[2] / self.tile_width) + self.border
        ymax = _math.ceil(self.window[3] / self.tile_height) + self.border
        xmin *= self.tile_width
        xmax *= self.tile_width
        ymin *= self.tile_height
        ymax *= self.tile_height
        if self.image_bounds[0] is not None:
            xmin = max(xmin, self.image_bounds[0])
        if self.image_bounds[2] is not None:
            xmax = min(xmax, self.image_bounds[2])
        if self.image_bounds[1] is not None:
            ymin = max(ymin, self.image_bounds[1])
        if self.image_bounds[3] is not None:
            ymax = min(ymax, self.image_bounds[3])
        return (xmin, ymin, xmax, ymax)


class Tiler(TileWindow):
    """Maintains the actual `PIL.Image` which we scroll around, and delegates
    producing tiles to a helper.

    The invariant we maintain is that the `PIL.Image` is always the same as
    the "buffer", and is displayed at (0,0) on the actual `tk.Canvas`.

    Scrolling is achieved by varying the display of the `tk.Canvas` (to give
    small movements quickly) using the :class:`image.Image`, and also moving
    the buffer (to achieve larger movements).
    """
    def __init__(self, tilewidth, tileheight=None, **kwargs):
        if tileheight is None:
            tileheight = tilewidth
        super().__init__(tilewidth, tileheight, **kwargs)
        self._lock = _threading.RLock()
        self._tiles = dict()
        self.window = (0,0,0,0)
        self.buffer_extent = (0,0,0,0)
        self._marsher = _TileJobMarsher()
        self._redrawer = None
        
    def update(self, location, size):
        """To be called with the values of `current_location` and `size` from
        :class:`image.Image`.

        :param location: `(left, top)` of the currently viewed image.
        :param size: `(width, height)` of the currently viewed image.
          Maybe `None` to indicate no update
        """
        x = self.buffer_extent[0] + location[0]
        y = self.buffer_extent[1] + location[1]
        if size is None:
            size = (self.window[2] - self.window[0], self.window[3] - self.window[1])
        self.window = (x, y, x + size[0], y + size[1])
        self._update()

    def _update(self):
        need = self.needed_buffer_extent
        if need == self.buffer_extent:
            return

        need_tile_space = (need[0] // self.tile_width, need[1] // self.tile_height,
            need[2] // self.tile_width, need[3] // self.tile_height)

        # If we don't have an infinite window, these can become negative if the view
        # is scrolled too far.
        need_width = max(0, need[2] - need[0])
        need_height = max(0, need[3] - need[1])
        new_image = PIL.Image.new("RGB", (need_width, need_height))
        
        tiles_needed = []
        for y in range(need_tile_space[3] - need_tile_space[1]):
            ty = y + need_tile_space[1]
            ydest = y * self.tile_height
            for x in range(need_tile_space[2] - need_tile_space[0]):
                tx = x + need_tile_space[0]
                xdest = x * self.tile_width
                if (tx, ty) in self._tiles:
                    new_image.paste(self._tiles[(tx, ty)], (xdest, ydest))
                else:
                    tiles_needed.append( (tx, ty) )

        with self._lock:
            keys = set(self._tiles.keys())
            for (tx, ty) in keys:
                if not (tx >= need_tile_space[0] and tx < need_tile_space[2] and
                    ty >= need_tile_space[1] and ty < need_tile_space[3]):
                    del self._tiles[(tx,ty)]
            self._image = new_image
            self.buffer_extent = need
            self._marsher.set_needed_tiles(tiles_needed)
        self._redraw()

    def get(self, timeout=None):
        """Get the next tile coords `(tx, ty)` which needs fetching.
        
        :param timeout: If not `None` then wait this many seconds for a job,
          before raising :class:`queue.Empty`
        """
        return self._marsher.get(timeout)

    def new_tile(self, tx, ty, tile):
        """Send a new tile at position `(tx, ty)`."""
        if tile is None:
            return
        new_image = None
        with self._lock:
            self._tiles[(tx, ty)] = tile
            x, y = tx * self.tile_width, ty * self.tile_height
            xdest = x - self.buffer_extent[0]
            ydest = y - self.buffer_extent[1]
            if (xdest >= 0 and ydest >= 0 and
                x + self.tile_width <= self.buffer_extent[2] and
                y + self.tile_height <= self.buffer_extent[3]):
                self._image.paste(tile, (xdest, ydest))
                new_image = self._image
        if new_image is not None:
            self.redrawer.new_image(new_image)

    class Redrawer():
        """Interface for the object whose job it is to actually display the
        image."""
        def __call__(self, image, offset):
            """Called on the GUI thread to indicate a new image.

            :param offset: A pair `(x,y)` which indicates the top-left corner
              of the image which we wish to view.
            """
            raise NotImplementedError()

        def new_image(self, image):
            """Called, may be not on the GUI thread, to indicate that the
            image has been updated.
            """
            raise NotImplementedError()

    @property
    def redrawer(self):
        """The instance of :class:`Redrawer`."""
        return self._redrawer

    @redrawer.setter
    def redrawer(self, v):
        self._redrawer = v

    def _redraw(self):
        if self.redrawer is None:
            return
        with self._lock:
            image = self._image
            x = self.window[0] - self.buffer_extent[0]
            y = self.window[1] - self.buffer_extent[1]
        self.redrawer(image, (x,y))


class _TileJobMarsher():
    """Pulled out functionality to think hard about synchronization."""
    def __init__(self):
        self._needed_tiles = []
        self._lock = _threading.RLock()
        self._job_queue = queue.Queue()

    def set_needed_tiles(self, tile_list):
        """Set a new list of needed tiles."""
        with self._lock:
            self._needed_tiles = tile_list
        self._job_queue.put(True)

    def get(self, timeout=None):
        """Get the next tile coords `(tx, ty)` which needs fetching.
        
        :param timeout: If not `None` then wait this many seconds for a job,
          before raising :class:`queue.Empty`
        """
        now = _time.clock()
        while timeout is None or _time.clock() < now + timeout:
            with self._lock:
                if len(self._needed_tiles) > 0:
                    return self._needed_tiles.pop()
            self._job_queue.get(timeout=timeout)
        raise queue.Empty()


class TileProvider():
    """The interface for providing a tile.  Will be run in a different thread,
    and so should not interact with the `tkinter` code.
    """
    def __call__(self, tx, ty):
        raise NotImplementedError()


class TileImage(image.Image):
    """The actual user class, a subclass of :class:`image.Image`.  Is a
    `tkinter` widget with dragable mouse support.
    
    :param parent: The parent `tkinter` widget.
    :param provider: The :class:`TileProvider` class.
    :param tilewidth: Width of each tile.
    :param tileheight: Height of each tile, or `None` for square tiles.
    """
    def __init__(self, parent, provider, tilewidth, tileheight=None, **kwargs):
        super().__init__(parent, free=True, **kwargs)
        self.mouse_handler = None
        self._provider = provider
        self._tiler = Tiler(tilewidth, tileheight)
        self._tiler.redrawer = self.Redrawer(self)
        self._pooler = self.Pooler(self)
        self._done = False
        self._lock = _threading.RLock()
        self._waiting_image = None
        self._pooler.start()
        self._tiler.update((0,0),(100,100))
        self.after(100, self._update)

    @property
    def tiler(self):
        """The :class:`Tiler` which is controlling tile creation."""
        return self._tiler

    def notify_of_gap(self, left, top, right, bottom):
        """Handles messages from the super class indicating the user has
        moved the image."""
        self._tiler.update(self.current_location, self.size)
    
    def destroy(self):
        self._done = True
        self._pooler.cancel()
        super().destroy()

    def move_tile_view_to(self, x, y):
        """Move the display so that the tile view has `(x,y)` in the upper
        left corner."""
        buffer_extent = self._tiler.buffer_extent
        buffer_width = buffer_extent[2] - buffer_extent[0]
        buffer_height = buffer_extent[3] - buffer_extent[1]
        xx = _math.floor(x / self._tiler.tile_width) * self._tiler.tile_width
        yy = _math.floor(y / self._tiler.tile_height) * self._tiler.tile_height
        self._tiler.buffer_extent = (xx, yy, xx + buffer_width, yy + buffer_height)
        self._tiler.update((x - xx,y - yy), None)

    @property
    def tile_window(self):
        """The current view in "tile space".  Querying :attr:`current_location`
        does not work, but this does, as it takes account of tile scrolling.

        :return: `(xmin, ymin, xmax, ymax)`
        """
        return self._tiler.window

    def _update(self):
        with self._lock:
            if self._waiting_image is not None:
                image = self._waiting_image
                self._waiting_image = None
            else:
                image = None
        if image is not None:
            self.set_image(image, None)
        if not self._done:
            self.after(100, self._update)

    def _new_image(self, image):
        """May be called off thread"""
        with self._lock:
            self._waiting_image = image

    def set_image(self, image, location):
        with self._lock:
            self._waiting_image = None
        super().set_image(image, location=location)

    @property
    def mouse_handler(self):
        v = super().mouse_handler
        return v.delegate

    @mouse_handler.setter
    def mouse_handler(self, v):
        image.Image.mouse_handler.fset(self, self.MouseHandler(self,v))

    class Pooler(_threading.Thread):
        def __init__(self, parent):
            super().__init__(daemon=True)
            self._parent = parent
            self._cancel = False
            self._logger = _logging.getLogger(__name__)

        def cancel(self):
            self._cancel = True

        def run(self):
            while not self._cancel:
                try:
                    tx, ty = self._parent._tiler.get(timeout=0.1)
                    tile = self._parent._provider(tx, ty)
                    self._parent._tiler.new_tile(tx, ty, tile)
                except queue.Empty:
                    pass
                except:
                    self._logger.exception("From tile provider...")

    class Redrawer(Tiler.Redrawer):
        def __init__(self, parent):
            self._parent = parent

        def __call__(self, image, offset):
            self._parent.set_image(image, offset)

        def new_image(self, image):
            self._parent._new_image(image)

    class MouseHandler(image.MouseHandler):
        def __init__(self, parent, delegate):
            self.parent = parent
            self.delegate = delegate
            self.offset = (0, 0)

        def handle(self, event, what):
            if self.delegate is not None:
                return self.delegate.handle(event, what)
            return False

        def notify(self, x, y):
            if self.delegate is not None:
                xx = x + self.parent._tiler.buffer_extent[0]
                yy = y + self.parent._tiler.buffer_extent[1]
                return self.delegate.notify(xx, yy)
