from . import colour, font, options, sample
from .full import FullEditor


class DefaultEditor(FullEditor):
    @property # @override
    def frames(self):
        return (
            (font.Frame, dict(row=0, column=0, rowspan=2, sticky='nw')),
            (sample.Frame, dict(row=2, column=0, columnspan=2, padx=60)),
            (self.buttons_frame, dict(row=2, column=2, sticky='se')),
            (options.Frame, dict(row=0, column=1, sticky='nw')),
            (colour.Colour, dict(row=1, column=1, sticky='nw')))
