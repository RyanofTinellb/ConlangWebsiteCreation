import SimpleHTTPServer
import SocketServer
from socket import error as socket_error
import threading
import os
import random
import webbrowser as web
import Tkinter as Tk
import tkFileDialog as fd
from editor_properties import EditorProperties
from properties_window import PropertiesWindow
from widgets import Widgets
from text_window import TextWindow
from itertools import izip
from cwsmeagol.site.page import Page
from cwsmeagol.utils import *
from cwsmeagol.translation import Translator


class Editor(Tk.Frame, object):
    """
    Base class for DictionaryEditor and TranslationEditor
    """
    def __init__(self, master=None):
        """
        Initialise an instance of the Editor class.
        :param directory (str):
        :param widgets (WidgetAmounts): number of each of headings, textboxes,
            radiobuttons to create.
        """
        super(Editor, self).__init__(master)
        self.master.title('Page Editor')
        self.master.protocol('WM_DELETE_WINDOW', self.quit)
        self.top = self.winfo_toplevel()

        self.properties = EditorProperties(caller=self.caller)

        self.language = Tk.StringVar()
        self.language.set(self.properties.language)
        self.translator = Translator(self.language.get())

        self.widgets = Widgets(self, headings=2, textboxes=1,
                                fontsize=self.properties.fontsize)
        commands = [
                ('<Control-N>', self.insert_new),
                ('<Control-b>', self.bold),
                ('<Control-i>', self.italic),
                ('<Control-k>', self.small_caps),
                ('<Control-n>', self.add_link),
                ('<Control-e>', self.example_no_lines),
                ('<Control-f>', self.example),
                ('<Control-t>', self.add_translation),
                ('<Control-o>', self.properties.site_open),
                ('<Control-s>', self.save),
                ('<Control-l>', self.load),
                ('<Control-m>', self.properties.markdown_refresh)
              ]
        self.widgets.add_commands('Text', commands)
        self.widgets.save_text = 'Save'
        commands = [
            (('<Prior>', '<Next>'), self.scroll_headings),
            ('<Return>', self.enter_headings)
          ]
        self.widgets.add_commands('Entry', commands)

        self.new_page = False

        self.server = None
        self.PORT = 41809
        self.start_server()

        self.entry = self.properties.site.root
        self.entry.content = self.entry.content or self.initial_content()
        self.widgets.fill_headings(self.properties.page)
        self.load()
        self.widgets.go_to(self.properties.position)

    def __getattr__(self, name):
        if name == 'language_code':
            return getattr(self.properties, 'language')
        else:
            raise AttributeError(name)

    @property
    def caller(self):
        return 'site'

    def refresh_random(self, event=None):
        """
        Show a certain number of random nonsense words using High Lulani phonotactics.
        """
        if self.words:
            self.widgets.information.set('\n'.join(self.words))
        return 'break'

    def scroll_headings(self, event):
        """
        Respond to PageUp / PageDown by changing headings, moving
            through the hierarchy.
        :param event (Event): which entry box received the KeyPress
        :param level (int): the level of the hierarchy that is being
            traversed.
        """
        root = self.properties.site.root
        heading = event.widget
        actual_level = self.widgets.headings.index(heading) + 2
        level = actual_level + root.level - 1
        direction = 1 if event.keysym == 'Next' else -1
        child = True
        # ascend hierarchy until correct level
        while self.entry.level > level:
            try:
                self.entry = self.entry.parent
            except AttributeError:
                break
        # traverse hierarchy sideways
        if self.entry.level == level:
            with ignored(IndexError):
                self.entry = self.entry.sister(direction)
        # descend hierarchy until correct level
        while self.entry.level < level:
            try:
                self.entry = self.entry.children[0]
            except IndexError:
                child = False
                break
        for heading_ in self.widgets.headings[level - root.level - 1:]:
            heading_.delete(0, Tk.END)
        while len(self.widgets.headings) > actual_level:
            self.widgets.remove_heading()
        while child and len(self.widgets.headings) < min(actual_level, 10):
            self.widgets.add_heading()
        if child:
            heading.insert(Tk.INSERT, self.entry.name)
            self.master.title('Editing ' + self.entry.name)
        return 'break'

    def enter_headings(self, event):
        """
        Go to the next heading, or load the entry
        """
        headings = self.widgets.headings
        level = headings.index(event.widget)
        try:
            headings[level + 1].focus_set()
        except IndexError:
            self.load()
        return 'break'

    def change_language(self, event=None):
        """
        Change the entry language to whatever is in the StringVar 'self.language'
        """
        self.translator = Translator(self.language.get())
        return 'break'

    def site_open(self, event=None):
        """
        Loop until a valid file is passed back, or user cancels
        """
        source = self.properties.open()
        self.reset()
        return 'break'

    def start_server(self):
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        while True:
            try:
                self.server = SocketServer.TCPServer(("", self.PORT), handler)
                handler.error_message_format = '''
                        <script>
                            window.location.replace('/404.html');
                        </script>'''
                break
            except socket_error:
                self.PORT += 1
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def open_in_browser(self, event=None):
        self.server.shutdown()
        self.server.server_close()
        web.open_new_tab(os.path.join('http://localhost:' + str(self.PORT), self.entry.link()))
        self.start_server()
        return 'break'

    def reset(self, event=None):
        """
        Reset the program.
        """
        self.entry = self.properties.site.root
        self.clear_interface()
        self.fill_headings(self.properties.page)
        self.load()

    def site_save(self, event=None):
        page = [heading.get() for heading in self.headings]
        self.properties.page = page
        self.properties.save()
        return 'break'

    def site_saveas(self, event=None):
        self.properties.saveas()
        return 'break'

    def site_properties(self, event=None):
        """
        Pass current site details to a new Properties Window, and then
            re-create the Site with the new values and renew the Links
        """
        properties_window = PropertiesWindow(self.properties)
        self.wait_window(properties_window)
        self.properties.site.root.name = self.properties.site.name
        self.properties.save()

    def site_publish(self, event=None):
        """
        Publish every page in the Site using the Site's own method
        """
        self.properties.site.publish()

    def load(self, event=None):
        """
        Find entry, manipulate entry to fit boxes, place in boxes.
        """
        widgets = self.widgets
        self.entry = self.find_entry(widgets.heading_contents)
        texts = self.prepare_entry(self.entry)
        widgets.display(texts)
        widgets.save_text = 'Save'
        return 'break'

    def add_translation(self, event):
        """
        Insert a transliteration of the selected text in the current language.
        Do sentence conversion if there is a period in the text, and word conversion otherwise.
        Insert an additional linebreak if the selection ends with a linebreak.
        """
        textbox = event.widget
        try:
            text = textbox.get(Tk.SEL_FIRST, Tk.SEL_LAST)
        except Tk.TclError:
            text = textbox.get(Tk.INSERT + ' wordstart', Tk.INSERT + ' wordend')
        length = len(text)
        with conversion(self.properties.markdown, 'to_markup') as converter:
            text = converter(text)
        example = re.match(r'\[[ef]\]', text) # line has 'example' formatting
        converter = self.translator.convert_sentence if '.' in text else self.translator.convert_word
        text = converter(text)
        if example:
            text = '[e]' + text
        with conversion(self.properties.markdown, 'to_markdown') as converter:
            text = converter(text)
        try:
            text += '\n' if textbox.compare(Tk.SEL_LAST, '==', Tk.SEL_LAST + ' lineend') else ' '
            textbox.insert(Tk.SEL_LAST + '+1c', text)
        except Tk.TclError:
            text += ' '
            textbox.mark_set(Tk.INSERT, Tk.INSERT + ' wordend')
            textbox.insert(Tk.INSERT + '+1c', text)
        textbox.mark_set(Tk.INSERT, '{0}+{1}c'.format(Tk.INSERT, str(len(text) + length)))
        self.widgets.html_to_tkinter()
        return 'break'

    def find_entry(self, headings):
        """
        Find the current entry based on what is in the heading boxes.
        This is the default method - other Editor programs may override this.
        Subroutine of self.load().
        :param headings (str[]): the texts from the heading boxes
        :return (Page):
        """
        entry = self.properties.site.root
        for heading in headings:
            if heading:
                try:
                    entry = entry[heading]
                except KeyError:
                    entry = Page(heading, entry, '').insert('end')
                    entry.content = self.initial_content(entry)
                    self.new_page = True
            else:
                break
        self.master.title('Editing ' + self.entry.name)
        return entry

    def list_pages(self, event=None):
        def text_thing(page):
            return ' ' * 2 * page.level + page.name
        text = '\n'.join(map(text_thing, self.properties.site))
        with conversion(self.properties.markdown, 'to_markdown') as converter:
            text = converter(text)
        textwindow = TextWindow(text)
        self.wait_window(textwindow)
        return 'break'

    def prepare_entry(self, entry):
        """
        Manipulate text taken from a single Page to suit a textbox.

        Default method, other Editors will override this.
        :param entry (Page): A Page instance carrying text.
        :param return (str):
        :called by: Editor.load()
        """
        text = entry.content
        text = remove_datestamp(text)
        with conversion(self.properties.linkadder, 'remove_links') as converter:
            text = converter(text)
        with conversion(self.properties.markdown, 'to_markdown') as converter:
            text = converter(text)
        return [text]

    def save(self, event=None):
        """
        Take text from box, manipulate to fit datafile, put in datafile, publish appropriate Pages.
        """
        if self.is_new:
            self.properties.site_properties()
        self.widgets.tkinter_to_html()
        texts = map(self.get_text, self.widgets.textboxes)
        if self.entry:
            self.prepare_texts(texts)
        self.publish(self.entry, self.properties.site, self.new_page)
        self.new_page = False
        self.widgets.html_to_tkinter()
        self.widgets.reset_textboxes()
        self.widgets.save_text.set('Save')
        return 'break'

    @property
    def is_new(self):
        if self.properties.site is None:
            return True
        elif not self.properties.source:
            return True
        elif self.properties.destination is None:
            return True
        return False

    @staticmethod
    def get_text(textbox):
        """
        Retrieves text from textbox.
        Default method - may be overriden by descendant classes.
        """
        return str(textbox.get(1.0, Tk.END + '-1c'))

    def prepare_texts(self, texts):
        """
        Modify entry with manipulated texts.
        Subroutine of self.save().
        Overrides parent method.
        :param texts (str[]): the texts to be manipulated and inserted.
        :param return (Nothing):
        """
        text = ''.join(texts)
        if self.entry.level and not text:
            self.entry.delete_htmlfile()
            self.entry.remove_from_hierarchy()
            self.reset()
        else:
            text = self.convert_texts(text, self.entry)
            # remove duplicate linebreaks
            text = re.sub(r'\n\n+', '\n', text)
            self.entry.content = text

    def convert_texts(self, text, entry):
        """
        Run conversions over text
        """
        with conversion(self.properties.markdown, 'to_markup') as converter:
            text = converter(text)
        with conversion(self.properties.linkadder, 'add_links') as converter:
            text = converter(text, entry)
        text = add_datestamp(text)
        return text

    @staticmethod
    def publish(entry, site, allpages=False):
        """
        Put entry contents into datafile, publish appropriate Pages.
        This is the default method - other Editor programs may override this.
        Subroutine of self.save()
        :param entry (Page):
        :return (nothing):
        """
        if allpages:
            site.publish()
        elif entry is not None:
            entry.publish(site.template)
        if site is not None:
            site.modify_source()
            site.update_json()

    @staticmethod
    def insert_characters(textbox, before, after=''):
        """
        Insert given text into a Text textbox, either around an
        insertion cursor or selected text, and move the cursor
        to the appropriate place.
        :param textbox (Tkinter Text): The Text into which the
        given text is to be inserted.
        :param before (str): The text to be inserted before the
        insertion counter, or before the selected text.
        :param after (str): The text to be inserted after the
        insertion cursor, or after the selected text.
        """
        try:
            text = textbox.get(Tk.SEL_FIRST, Tk.SEL_LAST)
            textbox.delete(Tk.SEL_FIRST, Tk.SEL_LAST)
            textbox.insert(Tk.INSERT, before + text + after)
        except Tk.TclError:
            textbox.insert(Tk.INSERT, before + after)
            textbox.mark_set(Tk.INSERT, Tk.INSERT + '-{0}c'.format(len(after)))

    def insert_formatting(self, event, tag):
        """
        Insert markdown for tags, and place insertion point between
        them.
        """
        with conversion(self.properties.markdown, 'find_formatting') as converter:
            self.insert_characters(event.widget, *converter(tag))

    def insert_markdown(self, event, tag):
        """
        Insert markdown for tags
        """
        with conversion(self.properties.markdown, 'find') as converter:
            self.insert_characters(event.widget, converter(tag))

    def example_no_lines(self, event):
        """
        Insert markdown for paragraph marking
        """
        self.insert_markdown(event, '[e]')
        return 'break'

    def example(self, event):
        """
        Insert markdown for paragraph marking
        """
        self.insert_markdown(event, '[f]')
        return 'break'

    def change_style(self, event, style):
        textbox = event.widget
        if style in textbox.tag_names(Tk.INSERT):
            try:
                textbox.tag_remove(style, Tk.SEL_FIRST, Tk.SEL_LAST)
            except Tk.TclError:
                textbox.tag_remove(style, Tk.INSERT)
        else:
            try:
                textbox.tag_add(style, Tk.SEL_FIRST, Tk.SEL_LAST)
            except Tk.TclError:
                textbox.tag_add(style, Tk.INSERT)

    def bold(self, event):
        """
        Use tags to bold and un-bold selected text
        """
        self.change_style(event, 'strong')
        return 'break'

    def italic(self, event):
        """
        Insert markdown for italic tags, and place insertion point between them.
        """
        self.change_style(event, 'em')
        return 'break'

    def small_caps(self, event):
        """
        Insert markdown for small-caps tags, and place insertion point between them.
        """
        self.change_style(event, 'small-caps')
        return 'break'

    def add_link(self, event):
        self.change_style(event, 'link')
        return 'break'

    def insert_spaces(self, event):
        self.insert_characters(event.widget, ' ' * 10)
        return 'break'

    def insert_new(self, event):
        self.entry.content = self.initial_content()
        self.load()
        return 'break'

    def select_paragraph(self, event=None):
        event.widget.tag_add('sel', Tk.INSERT + ' linestart', Tk.INSERT + ' lineend +1c')
        return 'break'

    def markdown_open(self, event=None):
        web.open_new_tab(self.properties.markdown.filename)

    def markdown_load(self, event=None):
        filename = fd.askopenfilename(
        filetypes=[('Sm\xe9agol Markdown File', '*.mkd')],
        title='Load Markdown')
        if filename:
            try:
                texts = map(self.get_text, self.widgets.textboxes)
                texts = map(self.properties.markdown.to_markup, texts)
                self.properties.markdown = Markdown(filename)
                self.properties.markdown = filename
                texts = map(self.properties.markdown.to_markdown, texts)
                for textbox, text in izip(self.widgets.textboxes, texts):
                    self.widgets.replace(textbox, text)
            except IndexError:
                mb.showerror('Invalid File', 'Please select a valid *.mkd file.')

    def markdown_refresh(self, event=None):
        try:
            self.widgets.tkinter_to_html()
            texts = map(self.get_text, self.widgets.textboxes)
            texts = map(self.properties.markdown.to_markup, texts)
            self.properties.markdown.refresh()
            texts = map(self.properties.markdown.to_markdown, texts)
            for textbox, text in self.widgets.textboxes, texts:
                self.widgets.replace(textbox, text)
            self.widgets.html_to_tkinter()
            self.widgets.information.set('OK')
        except AttributeError:
            self.widgets.information.set('Not OK')
        return 'break'

    def markdown_check(self, event=None):
        filename = self.properties.markdown.filename
        with open(filename) as markdown:
            original = markdown.read()
        intermediate = self.properties.markdown.to_markdown(original)
        translated = self.properties.markdown.to_markup(intermediate)
        output = ''
        for o, i, t in izip(*map(lambda x: x.splitlines(), [original, intermediate, translated])):
            if o != t:
                output += '{0} {3} {1} {3} {2}\n'.format(o, i, t, '-' * 5)
        textwindow = TextWindow(output)
        self.wait_window(textwindow)

    def quit(self):
        self.server.shutdown()
        page = [heading.get() for heading in self.widgets.headings]
        self.properties.page = page
        self.properties.language = self.language.get()
        self.properties.position = self.widgets.textboxes[0].index(Tk.INSERT)
        self.properties.fontsize = self.widgets.font.actual(option='size')
        self.properties.site_save()
        self.master.destroy()

    def initial_content(self, entry=None):
        """
        Return the content to be placed in a textbox if the page is new
        """
        if entry is None:
            entry = self.entry
        name = entry.name
        return '1]{0}\n'.format(name)


if __name__ == '__main__':
    e = Editor()
