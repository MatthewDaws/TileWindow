import pytest
import unittest.mock as mock

import tilewindow.tiler as tiler
import queue, itertools
import PIL.Image

def test_TileWindow_construct():
    tw = tiler.TileWindow(10, 20)
    assert tw.tile_width == 10
    assert tw.tile_height == 20

def test_TileWindow_construct_with_kwargs():
    tw = tiler.TileWindow(10, 20, image_bounds=(-10, -20, 50, 100))
    assert tw.image_bounds == (-10, -20, 50, 100)

    with pytest.raises(ValueError):
        tiler.TileWindow(10, 20, matt=1)

@pytest.fixture
def tw():
    return tiler.TileWindow(10, 20)

def test_TileWindow_image_bounds(tw):
    assert tw.image_bounds == (None, None, None, None)
    
    tw.image_bounds = [10, 20, 30, 40]
    assert tw.image_bounds == (10, 20, 30, 40)

    with pytest.raises(ValueError):
        tw.image_bounds = (1,2,3)

    with pytest.raises(ValueError):
        tw.image_bounds = (1,2,3,4,5)

    with pytest.raises(ValueError):
        tw.image_bounds = (10, 20, 20, 30)
        
def test_TileWindow_window(tw):
    tw.window = (0, 10, 100, 50)
    assert tw.window == (0, 10, 100, 50)

    with pytest.raises(ValueError):
        tw.window = (1,2,3,4,5)

    with pytest.raises(ValueError):
        tw.window = ("matt", 2, 3, 4)

def test_TileWindow_border(tw):
    assert tw.border == 1

    tw.border = 5
    assert tw.border == 5

    with pytest.raises(ValueError):
        tw.border = 0

    with pytest.raises(ValueError):
        tw.border = "a"

def test_TileWindow_buffer(tw):
    assert tw.buffer_extent == (0, 0, 0, 0)
    assert tw.buffer_width == 0
    assert tw.buffer_height == 0

    tw.buffer_extent = (-20, -40, 10, 20)
    assert tw.buffer_extent == (-20, -40, 10, 20)
    assert tw.buffer_width == 30
    assert tw.buffer_height == 60

    with pytest.raises(ValueError):
        tw.buffer_extent = 0, 1, 2, 3, 4

    with pytest.raises(ValueError):
        tw.buffer_extent = 0, "a"

    with pytest.raises(ValueError):
        tw.buffer_extent = 0, 10, 0, 20
        
def test_needed_buffer_extent(tw):
    # Tiles are 10 x 20
    tw.window = (-5, -19, 19, 21)
    assert tw.needed_buffer_extent == (-20, -40, 30, 60)

    tw.window = (-10, -19, 20, 39)
    assert tw.needed_buffer_extent == (-20, -40, 30, 60)
    
    tw.image_bounds = (0, 0, 20, 40)
    assert tw.needed_buffer_extent == (0, 0, 20, 40)

    tw.image_bounds = (0, 0, 80, 100)
    assert tw.needed_buffer_extent == (0, 0, 30, 60)

def test_needed_buffer_extent_with_bounds(tw):
    tw.image_bounds = (0,0,100,100)

    tw.window = (-5, -19, 19, 21)
    assert tw.needed_buffer_extent == (0, 0, 30, 60)

    tw.window = (0, 0, 90, 80)
    assert tw.needed_buffer_extent == (0, 0, 100, 100)

    tw.window = (0, 0, 100, 90)
    assert tw.needed_buffer_extent == (0, 0, 100, 100)

    tw.image_bounds = (0,0,None,None)
    tw.window = (0, 0, 100, 90)
    assert tw.needed_buffer_extent == (0, 0, 110, 120)


#############################################################################

@pytest.fixture
def tlr():
    return tiler.Tiler(20)

def test_tiler_constructs(tlr):
    assert tlr.tile_height == 20
    assert tlr.window == (0,0,0,0)
    assert tlr.buffer_extent == (0,0,0,0)

def test_update(tlr):
    tlr.update((10, 10), (35, 78))
    assert tlr.window == (10, 10, 45, 88)
    assert tlr.buffer_extent == (-20, -20, 80, 120)

    tlr.update((50,50), (35, 78))
    assert tlr.window == (30, 30, 65, 108)
    assert tlr.buffer_extent == (0, 0, 100, 140)

def test_get(tlr):
    tlr.update((10, 10), (35, 78))
    needed_tiles = set()
    with pytest.raises(queue.Empty):
        while True:
            needed_tiles.add(tlr.get(timeout=0.1))
    
    assert needed_tiles == set(itertools.product([-1,0,1,2,3], [-1,0,1,2,3,4,5]))

def test_get_replaces_midway(tlr):
    tlr.update((10, 10), (35, 78))
    for _ in range(4):
        tlr.get(timeout=0.1)
    
    # buffer is now (-20,80) x (-20, 120)
    tlr.update((0, 0), (80, 60))
    assert tlr.window == (-20, -20, 60, 40)

    needed_tiles = set()
    with pytest.raises(queue.Empty):
        while True:
            needed_tiles.add( tlr.get(timeout=0.1) )
    
    assert needed_tiles == set(itertools.product([-2,-1,0,1,2,3], [-2,-1,0,1,2]))

def test_new_tile(tlr):
    tile = PIL.Image.new("RGB", (20,20))
    for tile_key in itertools.product([-1,0,1,2,3], [-1,0,1,2,3,4,5]):
        tlr.new_tile(*tile_key, tile)

    tlr.update((10, 10), (35, 78))
    with pytest.raises(queue.Empty):
        tlr.get(timeout=0.1)

    tlr.update((0,20), (20,20))
    assert tlr.window == (-20, 0, 0, 20)
    needed_tiles = set()
    with pytest.raises(queue.Empty):
        while True:
            needed_tiles.add( tlr.get(timeout=0.1) )
    
    assert needed_tiles == set(itertools.product([-2], [-1,0,1]))

def test_redrawer(tlr):
    mock_drawer = mock.Mock()
    tlr.redrawer = mock_drawer
    tlr.update((10, 10), (35, 78))

    assert len(mock_drawer.call_args_list) == 1
    call = mock_drawer.call_args_list[0]
    assert isinstance(call[0][0], PIL.Image.Image)
    assert call[0][1] == (30, 30)

    tlr.update((30, 30), (40, 80))
    assert len(mock_drawer.call_args_list) == 1

    tlr.update((50,50), (35, 78))
    assert len(mock_drawer.call_args_list) == 2
    call = mock_drawer.call_args_list[1]
    assert call[0][1] == (30, 30)
