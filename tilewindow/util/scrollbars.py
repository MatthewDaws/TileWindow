"""
scrollbars
~~~~~~~~~~

Simple subclasses of the standard `tkinter.ttk` scroll-bars with the added
ability to detect when they are not needed (for example, so they can then be
hidden).
"""

import tkinter.ttk as ttk

class Scrollbar(ttk.Scrollbar):
    """A small extension of the :class:`tinker.ttk.Scrollbal` class which
    keeps track of whether the bar is current scrollable or not.

    Query to :attr:`needed` attribute to see if we need the bar or not.

    Set the :attr:`callback` to get a notification of when the :attr:`needed`
    changes.
    """
    def __init__(self, *args, **kwargs):
        self._our_needed = True
        self._our_callback = None
        super().__init__(*args, **kwargs)

    def set(self, start, end):
        """Listens to the usual `tkinter` method to change the scrollbar."""
        previous = self._our_needed
        if start <= 0 and end >= 1:
            self._our_needed = False
        else:
            self._our_needed = True
        super().set(start, end)
        if previous != self._our_needed and self._our_callback is not None:
            self._our_callback(self._our_needed)

    @property
    def needed(self):
        """Is the scroll bar needed (i.e. is the bar set to less than the whole
        bar)?"""
        return self._our_needed

    @property
    def callback(self):
        """The current callback on a change in the status of :attr:`needed`."""
        return self._our_callback

    @callback.setter
    def callback(self, v):
        self._our_callback = v

    def set_to_hide(self):
        """Change the `callback` to the default: either `grid`s or un-`grid`s
        the scroll bar as neccesary."""
        self.callback = self._hider

    def _hider(self, needed):
        if not needed:
            self.grid_remove()
        else:
            self.grid()


class Callback():
    """Specifies the interface need for the :attr:`callback` of
    :class:`Scrollbar`."""
    def __call__(self, needed):
        """Called when the "needed" status of the scroll bar changes.
    
        :param needed: `True` if then scrollbar is needed, and `False` is the
          bar is not needed.
        """
        raise NotImplementedError()
