"""
Use the package `tilemapbase` to display maps using tiles.  I.e. emulates
GoogleMaps, OpenStreetMap etc.
"""

import tilemapbase
from . import tiler, image
import PIL.Image as _Image
import PIL.ImageDraw as _ImageDraw
import math as _math

class MapImage(tiler.TileImage):
    """A `tkinter` widget which displays a draggable map.

    Is a subclass of :class:`tiler.TimeImage`.  We offer two ways of
    intercepting mouse movements:
      - For simple notification of the current longitude / latitude of the
        current location of the mouse pointer, set :attr:`map_mouse_handler`
        to an implementation of the interface :class:`MapMouseHandler`.
      - Alternative, set :attr:`mouse_handler` as for the class
        :class:`tiler.TimeImage`.  We capture such setting, so that both 
        notification methods will work together.

    :param parent: The parent `tkinter` widget.
    :param source: The source of tiles.  One of :class:`WebMercatorTiles` or
      one of the :class:`OrdnanceSurveyTiles` subclasses.
    """
    def __init__(self, parent, source):
        self._provider = source
        map_mouse_handler = None
        super().__init__(parent, self._provider, self._provider.tile_size)
        self.mouse_handler = None
        self.tiler.image_bounds = self._provider.bbox

    @property
    def map_mouse_handler(self):
        """The current instance of :class:`MapMouseHandler` or `None`."""
        return self._map_mouse_handler

    @map_mouse_handler.setter
    def map_mouse_handler(self, v):
        self._map_mouse_handler = v

    @property
    def mouse_handler(self):
        return super().mouse_handler.delegate

    @mouse_handler.setter
    def mouse_handler(self, v):
        tiler.TileImage.mouse_handler.fset(self, self._MapImageMouseHandler(self, v))

    def move_map_view_to(self, longitude, latitude):
        """Move to view so that this location is in the upper left of the
        window."""
        xx, yy = self._provider.lon_lat_to_tile_space(longitude, latitude)
        self.move_tile_view_to(xx, yy)

    def move_map_view_to_centre(self, longitude, latitude):
        """Move to view to be centred on this location.  Uses the current size
        of the window, which requires this widget to fully displayed by
        `tkinter` (i.e. calling this immediately after creating the widget is
        likely not to work.)"""
        xx, yy = self._provider.lon_lat_to_tile_space(longitude, latitude)
        xs, ys = self.size
        self.move_tile_view_to(xx - xs//2, yy - ys//2)

    def current_map_view(self):
        """The current bounding box which is displayed, in longitude and
        latitude.
        
        :return: `(longitude_min, latitude_min, longitude_max, latitude_max)`
        """
        xmin, ymin, xmax, ymax = self.tile_window
        return (*self._provider.tile_space_to_lon_lat(xmin, ymin),
            *self._provider.tile_space_to_lon_lat(xmax, ymax))

    class _MapImageMouseHandler(image.MouseHandlerChain):
        def __init__(self, parent, delegate=None):
            super().__init__(delegate)
            self.parent = parent
            self.delegate = delegate

        def notify(self, x, y):
            if self.parent.map_mouse_handler is not None:
                lon, lat = self.parent._provider.tile_space_to_lon_lat(x, y)
                self.parent.map_mouse_handler.notify(lon, lat)
            super().notify(x, y)


class MapMouseHandler():
    """Handle messages about where the mouse is."""
    def notify(self, longitude, latitude):
        """Called to notify that the mouse pointer is currently over this
        location.  Will be sent as :class:`math.nan` if outside of the
        coordinate system."""
        pass


class WebMercatorTiles():
    """Provides tiles from a tile provider using "web mercator" projection.

    Set the attribute :attr:`zoom` to change the zoom level.

    :param source: A :class:`tilemapbase.tiles.Tiles` instance giving the tile
      set to use.  Default is OpenStreetMap.
    """
    def __init__(self, source=None):
        if source is None:
            source = tilemapbase.tiles.OSM
        self._tile_provider = source
        self._empty = self._out_of_range_tile()
        self.zoom = 0

    def _out_of_range_tile(self):
        tile = _Image.new("L", (self.tile_size, self.tile_size), 255)
        draw = _ImageDraw.Draw(tile)
        draw.line((0,0,self.tile_size,self.tile_size))
        draw.line((0,self.tile_size,self.tile_size,0))
        return tile

    def __call__(self, tx, ty):
        maximum = 2 ** self._zoom
        if ty < 0 or ty >= maximum:
            return self._empty
        tx = tx % maximum
        return self._tile_provider.get_tile(tx, ty, self._zoom)

    def lon_lat_to_tile_space(self, lon, lat):
        """Convert to actual tile coordinates."""
        scale = 2 ** self._zoom * self.tile_size
        x, y = tilemapbase.project(lon, lat)
        return x * scale, y * scale

    def tile_space_to_lon_lat(self, x, y):
        """Convert actual tile coordinates to longitude and latitude.
        Returns :class:`math.nan` if not in range."""
        scale = 2 ** self._zoom * self.tile_size
        x, y = x / scale, y / scale
        x = x % 1
        if x < 0 or y < 0 or x > 1 or y > 1:
            return _math.nan, _math.nan
        return tilemapbase.to_lonlat(x, y)

    @property
    def zoom(self):
        """The current zoom level, between 0 and :attr:`maxzoom` inclusive."""
        return self._zoom

    @zoom.setter
    def zoom(self, v):
        v = int(v)
        if v < 0 or v > self.maxzoom:
            raise ValueError()
        self._zoom = v

    @property
    def tile_size(self):
        return self._tile_provider.tilesize

    @property
    def maxzoom(self):
        return self._tile_provider.maxzoom
    
    @property
    def bbox(self):
        size = (2 ** self._zoom) * self.tile_size
        return (None, 0, None, size)


class OrdnanceSurveyTiles():
    """Provides tiles from Ordnance Survey sources.  Base class which is
    over-ridden to specify the tiles."""
    def __init__(self):
        self._empty = self._out_of_range_tile()

    def __call__(self, tx, ty):
        x = tx * self._tile_provider.size_in_meters + 0.5
        y = (-1 - ty) * self._tile_provider.size_in_meters + 0.5
        if (x < self._tile_provider.bounding_box[0]
                or y < self._tile_provider.bounding_box[1] - self.tile_size
                or x >= self._tile_provider.bounding_box[2] - self.tile_size
                or y >= self._tile_provider.bounding_box[3]):
            tile = self._empty
        else:
            try:
                code = tilemapbase.ordnancesurvey.coords_to_os_national_grid(x, y)
                tile = self._tile_provider(code)
            except:
                tile = self._empty
        return tile

    @property
    def tile_size(self):
        return self._tile_provider.tilesize

    def tile_space_to_lon_lat(self, x, y):
        """Convert from the tile coordinates to longitude and latitude."""
        x = x / self.tile_size * self._tile_provider.size_in_meters
        y = -y / self.tile_size * self._tile_provider.size_in_meters
        return tilemapbase.ordnancesurvey.to_lonlat(x, y)

    def lon_lat_to_tile_space(self, lon, lat):
        """Convert to tile coordinates."""
        x, y = tilemapbase.ordnancesurvey.project(lon, lat)
        xx = _math.floor(x * self.tile_size / self._tile_provider.size_in_meters)
        yy = _math.floor(-y * self.tile_size / self._tile_provider.size_in_meters)
        return xx, yy

    @property
    def bbox(self):
        bbox = [x * self._tile_provider.tilesize / self._tile_provider.size_in_meters
                for x in self._tile_provider.bounding_box]
        bbox[1], bbox[3] = -bbox[3], -bbox[1]
        return bbox

    def _out_of_range_tile(self):
        tile = _Image.new("L", (self.tile_size, self.tile_size), 255)
        draw = _ImageDraw.Draw(tile)
        draw.line((0,0,self.tile_size,self.tile_size))
        draw.line((0,self.tile_size,self.tile_size,0))
        return tile


class OSOverView(OrdnanceSurveyTiles):
    """A very large scale map of the UK and neighbouring countries.
    This is one of a number of single files of size 4000 x 3200.

    Use the attributes :attr:`filenames` and :attr:`filename_choice`
    to change which file to use.
    """
    def __init__(self):
        self._tile_provider = tilemapbase.ordnancesurvey.OverView()
        super().__init__()

    @property
    def filenames(self):
        return self._tile_provider.filenames

    @property
    def filename_choice(self):
        return self._tile_provider.filename

    @filename_choice.setter
    def filename_choice(self, v):
        self._tile_provider.filename = v


class OSMiniScale(OrdnanceSurveyTiles):
    """A large scale map of the UK of size 7000 x 13000.

    Use the attributes :attr:`filenames` and :attr:`filename_choice`
    to change which file to use.
    """
    def __init__(self):
        tp = tilemapbase.ordnancesurvey.MiniScale()
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, 200)
        super().__init__()

    @property
    def filenames(self):
        return self._tile_provider.filenames

    @property
    def filename_choice(self):
        return self._tile_provider.filename

    @filename_choice.setter
    def filename_choice(self, v):
        self._tile_provider.filename = v


class OSTwoFiftyScale(OrdnanceSurveyTiles):
    """1:250 000 Scale Colour Raster tiles.  25 metres to the pixel."""
    def __init__(self):
        tp = tilemapbase.ordnancesurvey.TwoFiftyScale()
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, 200)
        super().__init__()
    

class OSVectorMapDistrict(OrdnanceSurveyTiles):
    """OS VectorMap District.  2.5 metres to the pixel.
    
    :param scale: If not 1, then the fraction to scale the tile size by.
    """
    def __init__(self, scale=1, size=200):
        tp = tilemapbase.ordnancesurvey.VectorMapDistrict()
        if scale != 1:
            tp = tilemapbase.ordnancesurvey.TileScalar(tp, int(4000 * scale + 0.5))
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, size)
        super().__init__()
    

class OSVectorMapDistrictQuarter(OSVectorMapDistrict):
    """OS VectorMap District, quarter size.  10 metres to the pixel."""
    def __init__(self):
        super().__init__(scale=0.25, size=250)

class OSVectorMapDistrictHalf(OSVectorMapDistrict):
    """OS VectorMap District, halved size.  5 metres to the pixel."""
    def __init__(self):
        super().__init__(scale=0.5, size=250)


class OSOpenMapLocal(OrdnanceSurveyTiles):
    """OS OpenMap Local.  1 metre to the pixel.
    
    :param scale: If not 1, then the fraction to scale the tile size by.
    """
    def __init__(self, scale=1, size=200):
        tp = tilemapbase.ordnancesurvey.OpenMapLocal()
        if scale != 1:
            tp = tilemapbase.ordnancesurvey.TileScalar(tp, int(5000 * scale + 0.5))
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, size)
        super().__init__()


class OSOpenMapLocalHalf(OSOpenMapLocal):
    """OS OpenMap Local scaled by half.  2 metres to the pixel.
    """
    def __init__(self):
        super().__init__(scale=0.5, size=250)


class OS25kRaster(OrdnanceSurveyTiles):
    def __init__(self, scale=1):
        tp = tilemapbase.ordnancesurvey.TwentyFiveRaster()
        if scale != 1:
            tp = tilemapbase.ordnancesurvey.TileScalar(tp, int(4000 * scale + 0.5))
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, 200)
        super().__init__()


class OS25kRasterHalf(OS25kRaster):
    def __init__(self):
        super().__init__(scale=0.5)


class OS25kRasterQuarter(OS25kRaster):
    def __init__(self):
        super().__init__(scale=0.25)


class OSMasterMap1000(OrdnanceSurveyTiles):
    def __init__(self, scale=1, size=200):
        tp = tilemapbase.ordnancesurvey.MasterMap()
        if scale != 1:
            tp = tilemapbase.ordnancesurvey.TileScalar(tp, int(3200 * scale + 0.5))
        self._tile_provider = tilemapbase.ordnancesurvey.TileSplitter(tp, size)
        super().__init__()


class OSMasterMap1000Half(OSMasterMap1000):
    def __init__(self):
        super().__init__(scale=0.5)


class OSMasterMap1000Quarter(OSMasterMap1000):
    def __init__(self):
        super().__init__(scale=0.25)
