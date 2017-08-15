import pytest
import unittest.mock as mock

import tilewindow.tilemap as tilemap

import PIL.Image
import numpy as np

@pytest.fixture
def icon():
    return PIL.Image.new("RGBA", (16,16))

def test_DroppedPins_init(icon):
    dp = tilemap.DroppedPins(icon, (8,15), None)

    tile = mock.Mock()
    out = dp.process(tile, None, None)
    assert out is tile

def test_DroppedPins_setter(icon):
    source = mock.Mock()
    source.lon_lat_to_tile_space.return_value = (5,6)
    dp = tilemap.DroppedPins(icon, (8,15), source)

    dp.locations = (1, 2)
    np.testing.assert_allclose(dp.locations, [[5,6]])
    source.lon_lat_to_tile_space.assert_called_with(1,2)

    dp.locations = [(1, 2), [3,2]]
    np.testing.assert_allclose(dp.locations, [[5,6], [5,6]])
    source.lon_lat_to_tile_space.assert_called_with(3,2)


    with pytest.raises(ValueError):
        dp.locations = (5,6,7)

def test_DroppedPins_process(icon):
    source = mock.Mock()
    source.lon_lat_to_tile_space.return_value = (5,6)
    dp = tilemap.DroppedPins(icon, (8,15), source)
    dp.locations = (1.5, 1.8)

    tile = mock.Mock()
    tile.mode = "RGB"
    tile.width = 200
    tile.height = 100
    
    out = dp.process(tile, 0, 0)
    assert out == tile.copy.return_value
    assert len(out.paste.call_args_list) == 1
    assert out.paste.call_args_list[0][0][1] == (5-8, 6-15)

    tile.mode = "L"
    out = dp.process(tile, 0, 0)
    assert out == tile.convert.return_value
    assert len(out.paste.call_args_list) == 1
    assert out.paste.call_args_list[0][0][1] == (5-8, 6-15)

    out = dp.process(tile, 1, 0)
    assert out is tile

    tile.reset_mock()
    out = dp.process(tile, -1, 0)
    assert out == tile.convert.return_value
    assert len(out.paste.call_args_list) == 1
    assert out.paste.call_args_list[0][0][1] == (205-8, 6-15)
