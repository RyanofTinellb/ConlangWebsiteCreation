import Tkinter as Tk
from editor_properties import EditorProperties

class PropertiesWindow(Tk.Toplevel, object):

    """

    :param properties: (EditorProperties)
    """
    def __init__(self, properties=None, master=None):
        super(PropertiesWindow, self).__init__(master)
        self.properties = properties or EditorProperties()
        commands = dict(done=self.finish_window, cancel=self.cancel_window)
        self.property_frames = []
        for row, property_ in enumerate(self.properties.template):
            property_frame = PropertyFrame(self, row, self.properties, commands)
            self.property_frames.append(property_frame)
        self.configure_buttons(row+1, commands)
        self.property_frames[0].entry.focus_set()

    def configure_buttons(self, row, commands):
        done_button = Tk.Button(self, text='OK', command=commands['done'])
        cancel_button = Tk.Button(self, text='Cancel', command=commands['cancel'])
        done_button.grid(row=row, column=3, sticky=Tk.E+Tk.W)
        cancel_button.grid(row=row, column=2, sticky=Tk.E)

    def finish_window(self, event=None):
        """
        Set values to site values and links values from the properties
            window, and then disable the window
        """
        for frame in self.property_frames:
            property_frame.update()
        self.destroy()

    def cancel_window(self, event=None):
        """
        Do nothing if cancel button pressed
        """
        self.destroy()

class PropertyFrame:
    """
    Wrapper class for one row of a PropertiesWindow
    """
    def __init__(self, master, row, properties, commands):
        """
        Create a row of the properties window
        """
        self.properties = properties
        self.template = properties.template[row]
        self.config = properties.config
        self.__dict__.update(self.template)

        value = self.config[self.owner]

        self.checkvar, self.entryvar = Tk.IntVar(), Tk.StringVar()
        self.entry = self.check = self.button = self.label = None
        if self.check:
            self.checkvar.set([adder['type'] for adder in value].includes(self.property))
            self.check = Tk.Checkbutton(master, variable=self.checkvar)
            self.check.grid(row=row, column=0)
        self.label = Tk.Label(master, text=self.name)
        self.label.grid(row=row, column=1, sticky=Tk.W)
        if self.browse:
            try:
                text = value[self.property]
            except TypeError:
                text = [prop['filename'] for prop in value if prop['type'] == self.property]
            self.entryvar.set(text)
            self.entry = Tk.Entry(master, width=50, textvariable=self.entryvar)
            self.entry.bind('<Return>', commands['done'])
            self.entry.bind('<Escape>', commands['cancel'])
            self.entry.grid(row=row, column=2)
            if self.browse == 'folder':
                self.browse = self.browse_folder
            else:
                self.browse = self.file_browser((self.browse['text'], self.browse['extension']))
            self.button = Tk.Button(master, text='Browse...', command=self.browse)
            self.button.grid(row=row, column=3)

    def browse_folder(self):
        """
        Allow the user to browse for a folder
        """
        filename = fd.askdirectory()
        self.insert(filename)
        self.entry.focus_set()

    def file_browser(self, filetype):
        def browse_file():
            """
            Allow the user to browse for a file of a given filetype

            :param filetype: (str()) The usual tuple passed to a Tk.FileDialog
            """
            filename = fd.askopenfilename(filetypes=[filetype], title='Select File')
            self.insert(filename)
            if filename:
                with ignored(AttributeError):
                    self.check.select()
            self.entry.focus_set()
        return browse_file

    def insert(self, text=None):
        """
        Insert text into the appropriate textbox
        """
        if text:
            self.entry.delete(0, Tk.END)
            self.entry.insert(Tk.INSERT, text)

    def get(self):
        return dict(owner=self.owner, property=self.property,
                check=self.checkvar.get(), value=self.entryvar.get())
