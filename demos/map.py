# Demos a "web mapping" -like application.
# Out the box supports a variety of internet tile sources.
# Can also be used with Open Data tiles from the UK Ordnance Survey: specify
#   the path to search on the command line.
# Can also be used with a few non-Open Data tiles from the UK Ordnance Survey.
#   Specify the paths to search as additional options, in the order
#   [25k Raster Tiles path] [1-to-1000 MasterMap Tiles path]

import sys

try:
    import tilemapbase
except:
    print("Failed to import `tilemapbase`.  Please install from https://github.com/MatthewDaws/TileMapBase")
    sys.exit(1)

tilemapbase.start_logging()

import os
sys.path.insert(0, os.path.abspath(".."))

import tilewindow
import tilewindow.tilemap as tilemap

if len(sys.argv) < 2:
    path = os.path.join("..", "..", "..", "Data", "OS_OpenMap")
    # TODO: Test with a dummy directory...
else:
    path = sys.argv[1]
print("Scanning path '{}' for Ordnance Survey tiles...".format(path))
try:
    tilemapbase.ordnancesurvey.init(path)
except:
    print("Failed.  You can set the path by running as 'python {} path'.  If you have no OS tiles, pass '.' as the path.".format(sys.argv[0]))
    sys.exit(1)

#if len(sys.argv) >= 3:
#    path = sys.argv[2]
#    tilemapbase.ordnancesurvey.TwentyFiveRaster.init(path)
path = os.path.join("..", "..", "..", "Data", "DigiMap", "raster-25k")
tilemapbase.ordnancesurvey.TwentyFiveRaster.init(path)
#if len(sys.argv) >= 4:
#    path = sys.argv[3]
#    tilemapbase.ordnancesurvey.MasterMap.init(path)
path = os.path.join("..", "..", "..", "Data", "DigiMap", "mastermap_1_to_1000_png")
tilemapbase.ordnancesurvey.MasterMap.init(path)

import tkinter as tk
import tkinter.ttk as ttk
import math

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.add_widgets()

    def add_widgets(self):
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0)
        ttk.Button(frame, text="Switch to Internet tiles", command=self.internet_tiles).grid(row=0, column=0)
        ttk.Button(frame, text="Switch to Ordnance Survey tiles", command=self.os_tiles).grid(row=0, column=1)
        self._info_label = ttk.Label(frame)
        self._info_label.grid(row=1, column=0, columnspan=2)
        self._control_frame = ttk.Frame(self)
        self._control_frame.grid(row=1, column=0)
        self._canvas_frame = ttk.Frame(self)
        self._canvas_frame.grid(row=2, column=0, sticky=tk.NSEW)
        tilewindow.util.stretch(self, [2], [0])
        tilewindow.util.stretch(self._canvas_frame, [0], [0])

        self.os_tiles()

    def _del_children(self, widget):
        for w in widget.winfo_children():
            w.destroy()

    def internet_tiles(self):
        self._del_children(self._control_frame)
        frame = ttk.Frame(self._control_frame)
        frame.grid(row=0, column=0)
        self._web_sources = {0 : tilemapbase.tiles.OSM}
        self._web_choice = tk.IntVar()
        for col, name in enumerate(["Open Street Map"]):
            ttk.Radiobutton(frame, text=name, value=col, variable=self._web_choice, command=self._web_new_choice).grid(row=0, column=col)
        
        frame = ttk.Frame(self._control_frame)
        frame.grid(row=1, column=0)
        self._web_zoom_level = ttk.Label(frame)
        self._web_zoom_level.grid(row=0, column=0)
        ttk.Button(frame, text="Zoom In", command=self._web_zoom_in).grid(row=0, column=1)
        ttk.Button(frame, text="Zoom Out", command=self._web_zoom_out).grid(row=0, column=2)

        self._location = None
        self._web_zoom = 10
        self._set_web_choice(0)
        self._set_web_zoom(10)

    def _set_web_zoom(self, zoom):
        zoom = max(0, zoom)
        zoom = min(zoom, self._web_source.maxzoom)
        self._web_zoom = zoom
        self._web_zoom_level["text"] = "Zoom: {}".format(self._web_zoom)

    def _web_zoom_in(self):
        self._set_web_zoom(self._web_zoom + 1)
        self._web_new_choice()

    def _web_zoom_out(self):
        self._set_web_zoom(self._web_zoom - 1)
        self._web_new_choice()

    def _web_new_choice(self, event=None):
        choice = int(self._web_choice.get())
        self._set_web_choice(choice)

    def _set_web_choice(self, choice):
        self._web_choice.set(choice)
        self._web_source = tilemap.WebMercatorTiles(self._web_sources[choice])
        self._web_source.zoom = self._web_zoom
        self._show_tiles(self._web_source, self.MouseHandlerWebMercator(self))

    def os_tiles(self):
        self._del_children(self._control_frame)
        frame = ttk.Frame(self._control_frame)
        frame.grid(row=0, column=0)
        self._os_sources = {0 : tilemap.OSOverView(),
            1 : tilemap.OSMiniScale(),
            2 : tilemap.OSTwoFiftyScale(),
            3 : tilemap.OSVectorMapDistrictQuarter(),
            4 : tilemap.OSVectorMapDistrictHalf(),
            5 : tilemap.OSVectorMapDistrict(),
            6 : tilemap.OSOpenMapLocalHalf(),
            7 : tilemap.OSOpenMapLocal()}
        self._os_choice = tk.IntVar()
        for col, name in enumerate(["Overview", "MiniScale", "250k", "District 1/4", "District 1/2", "District", "Local 1/2", "Local"]):
            ttk.Radiobutton(frame, text=name, value=col, variable=self._os_choice, command=self._os_new_choice).grid(row=0, column=col)

        have25k, haveMM = False, False
        try:
            codes = tilemapbase.ordnancesurvey.TwentyFiveRaster.found_tiles()
            have25k = len(codes) > 0
        except:
            pass
        try:
            codes = tilemapbase.ordnancesurvey.MasterMap.found_tiles()
            haveMM = len(codes) > 0
        except:
            pass
        if have25k or haveMM:
            col = 0
            if have25k:
                self._os_sources[10] = tilemap.OS25kRasterQuarter()
                self._os_sources[11] = tilemap.OS25kRasterHalf()
                self._os_sources[12] = tilemap.OS25kRaster()
                for v, name in zip(range(10, 13), ["25k Raster 1/4", "25k Raster 1/2", "25k Raster"]):
                    ttk.Radiobutton(frame, text=name, value=v, variable=self._os_choice, command=self._os_new_choice).grid(row=1, column=col)
                    col += 1
            if haveMM:
                self._os_sources[20] = tilemap.OSMasterMap1000Quarter()
                self._os_sources[21] = tilemap.OSMasterMap1000Half()
                self._os_sources[22] = tilemap.OSMasterMap1000()
                for v, name in zip(range(20, 23), ["MasterMap 1/4", "MasterMap 1/2", "MasterMap"]):
                    ttk.Radiobutton(frame, text=name, value=v, variable=self._os_choice, command=self._os_new_choice).grid(row=1, column=col)
                    col += 1
        self._location = None
        self._set_os_choice(1)

    def _os_new_choice(self, event=None):
        choice = int(self._os_choice.get())
        self._set_os_choice(choice)

    def _set_os_choice(self, choice):
        self._os_choice.set(choice)
        self._show_tiles(self._os_sources[choice], self.MouseHandlerOrdnance(self))

    def _show_tiles(self, source, mouse_handler):
        if hasattr(self, "_map_image"):
            x1, y1, x2, y2 = self._map_image.current_map_view()
            self._location = (x1+x2)/2, (y1+y2)/2
            self._map_image.destroy()
        if self._location is None:
            self._location = self._default_start_point()
        self._map_image = tilemap.MapImage(self._canvas_frame, source)
        self._map_image.move_map_view_to(*self._location)
        self._map_image.grid(sticky=tk.NSEW)
        self._map_image.map_mouse_handler = mouse_handler
        self._map_image.mouse_handler = tilewindow.image.MouseCursorHandler(self._map_image, None)
        self._map_image["cursor"] = "crosshair"
        self.after(100, lambda : self._map_image.move_map_view_to_centre(*self._location))

    def _default_start_point(self):
        x, y = tilemapbase.ordnancesurvey.os_national_grid_to_coords("SE 29700 34000")
        lon, lat = tilemapbase.ordnancesurvey.to_lonlat(x, y)
        return lon, lat

    class MouseHandlerWebMercator(tilemap.MapMouseHandler):
        def __init__(self, parent):
            self.parent = parent

        def notify(self, longitude, latitude):
            if longitude is math.nan:
                self.parent._info_label["text"] = ""
            else:
                self.parent._info_label["text"] = "Longitude / Latitude : {:.6f},{:.6f}".format(longitude, latitude)

    class MouseHandlerOrdnance(tilemap.MapMouseHandler):
        def __init__(self, parent):
            self.parent = parent

        def notify(self, longitude, latitude):
            x, y = tilemapbase.ordnancesurvey.project(longitude, latitude)
            code = tilemapbase.ordnancesurvey.coords_to_os_national_grid(x + 0.49, y + 0.49)
            self.parent._info_label["text"] = "Longitude / Latitude : {:.6f},{:.6f} == {}".format(longitude, latitude, code)


root = App()
root.mainloop()
