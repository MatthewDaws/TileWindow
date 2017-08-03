"""
util
~~~~

Some basic `tkinter` utilities
"""

#import tkinter as tk

def screen_size(widget):
    """Find the dimensions of the screen.
    
    :param widget: Window object
    
    :return: `(width, height)`
    """
    return (widget.winfo_screenwidth(), widget.winfo_screenheight())

def centre_window(window, width=None, height=None):
    """Set the window to be of the given size, centred on the screen.
    
    :param width: Width to set the window to.  If `None` then don't change.
    :param height: Height to set the window to.  If `None` then don't change.
    """
    if width is None or height is None:
        window.update_idletasks()
        if width is None:
            width = window.winfo_reqwidth()
        if height is None:
            height = window.winfo_reqheight()
    w, h = screen_size(window)
    x, y = (w - width) // 2, (h - height) // 2
    minw, minh = window.minsize()
    minw = min(minw, width)
    minh = min(minh, height)
    window.minsize(minw, minh)
    window.geometry("{}x{}+{}+{}".format(width, height, x, y))

def centre_window_percentage(window, width_percentage, height_percentage):
    """Set the window to be the given percentages of the total screen size,
    cented on the screen."""
    w, h = screen_size(window)
    centre_window(window, w * width_percentage // 100, h * height_percentage // 100)

def stretch(widget, rows=None, columns=None):
    """Configure the "weight" of the passed rows and/or columns for the widget.
    
    :rows: `None`, or iterable of row indicies.  For each entry, we call
      `widget.rowconfigure(row, weight=1)`
    :columns: `None`, or iterable of column indicies.
    """
    if rows is not None:
        for r in rows:
            widget.rowconfigure(r, weight=1)
    if columns is not None:
        for c in columns:
            widget.columnconfigure(c, weight=1)
