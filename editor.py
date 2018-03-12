import Tkinter as Tk
from cwsmeagol.editor.editor import Editor
from cwsmeagol.editor.dictionary_editor import DictionaryEditor
from cwsmeagol.editor.translation_editor import TranslationEditor


class Smeagol(Tk.Frame, object):
    def __init__(self):
        super(Smeagol, self).__init__(master=None)
        self.master.protocol('WM_DELETE_WINDOW', self.quit)
        editors = [self.open_site, self.open_dictionary, self.open_translation]
        texts = ['Site', 'Dictionary', 'Translation']
        for i, (editor, text) in enumerate(zip(editors, texts)):
            button = Tk.Button(command=editor, text=text, height=8, width=14)
            button.grid(column=i, row=0)

    def open_editor(self, editor):
        top = Tk.Toplevel()

    def open_site(self):
        self.open_editor(Editor)

    def open_dictionary(self):
        self.open_editor(DictionaryEditor)

    def open_translation(self):
        self.open_editor(TranslationEditor)


Smeagol().mainloop()
