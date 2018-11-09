from site_editor import SiteEditor, Tk
from cwsmeagol.site.page import Page
from cwsmeagol.utils import *

class DictionaryEditor(SiteEditor):
    def __init__(self, master=None, current=None):
        """

        """
        # initialise instance variables
        self.entry = None
        self.history = []
        self.current = -1

        super(DictionaryEditor, self).__init__(master, current)
        commands = [
            ('<Control-r>', self.refresh_random),
            ('<Control-=>', self.add_definition),
            ('<Prior>', self.scroll_history),
            ('<Next>', self.scroll_history),
            ('<Button-2>', self.set_jump_to_entry),
            ('<Control-Return>', self.jump_to_entry)

        ]
        self.add_commands('Text', commands)
        self.heading = self.headings[0]
        self.font.config(family='Courier New')
        self.master.title('Editing Dictionary')

    def jump_to_entry(self, event):
        textbox = event.widget
        try:
            borders = (Tk.SEL_FIRST, Tk.SEL_LAST)
            entry = textbox.get(*borders)
        except Tk.TclError:
            entry = self.select_word(event)
        self.save_page()
        self.heading.delete(0, Tk.END)
        self.heading.insert(0, entry)
        self.load()

    def set_jump_to_entry(self, event):
        textbox = event.widget
        textbox.mark_set(Tk.INSERT, Tk.CURRENT)
        self.jump_to_entry(event)
        return 'break'

    @property
    def caller(self):
        return 'dictionary'

    def scroll_headings(self, event):
        if event.keysym == 'Prior':
            if self.current > 0:
                self.current -= 1
                self.heading.delete(0, Tk.END)
                self.heading.insert(0, self.markdown.to_markdown(
                    self.history[self.current]))
        elif event.keysym == 'Next':
            if self.current < len(self.history) - 1:
                self.current += 1
                self.heading.delete(0, Tk.END)
                self.heading.insert(0, self.markdown.to_markdown(
                    self.history[self.current]))
        return 'break'

    def scroll_history(self, event):
        self.scroll_headings(event)
        self.load()
        return 'break'

    def previous_entry(self, event):
        m = self.markdown.to_markdown
        self.heading.delete(0, Tk.END)
        self.heading.insert(0, m(self.entry.previous.name))
        self.load()

    def next_entry(self, event):
        m = self.markdown.to_markdown
        self.heading.delete(0, Tk.END)
        self.heading.insert(0, m(self.entry.next_node.name))
        self.load()

    def keep_history(self, heading):
        """
        Keep track of which entries have been loaded
        """
        if not self.history or heading != self.history[self.current]:
            try:
                self.history[self.current + 1] = heading
                self.history = self.history[:self.current + 2]
            except IndexError:
                self.history.append(heading)
            self.current += 1

    def add_definition(self, event=None):
        """
        Insert the markdown for entry definition, and move the insertion pointer to allow for immediate input of the definition.
        """
        widget = event.widget
        m = self.markdown.to_markdown
        self.insert_characters(
            widget, m('<div class="definition">'), m('</div>'))
        return 'break'

    def find_entry(self, headings):
        """
        Find the current entry based on what is in the heading boxes.
        Overrides SiteEditor.find_entry.
        Subroutine of self.load().
        :param headings (str[]): the texts from the heading boxes
        :return (Page):
        """
        heading = sellCaps(headings[0])
        site = self.site
        with conversion(self.markdown, 'to_markup') as converter:
            heading = converter(heading)
        try:
            entry = site[heading]
        except KeyError:
            initial = re.sub(r'.*?(\w).*', r'\1',
                urlform(heading)).capitalize()
            entry = Page(heading, site[initial], '', newpage=True)
            entry.content = self.initial_content(entry)
        self.keep_history(heading)
        self.master.title('Editing Dictionary: ' + self.entry.name)
        return entry

    def prepare_entry(self, entry):
        text = super(DictionaryEditor, self).prepare_entry(entry)[0]
        text = text.splitlines(True)
        text[0] = buyCaps(text[0])
        text = ''.join(text)
        return [text]

    def prepare_texts(self, texts):
        """
        Modify entry with manipulated texts.
        Subroutine of self.save().
        Overrides SiteEditor.prepare_texts()
        :param entry (Page): the entry in the datafile to be modified.
        :param texts (str[]): the texts to be manipulated and inserted.
        :param markdown (Markdown): a Markdown instance to be applied to the texts. If None, the texts are not changed.
        :param return (Nothing):
        """
        texts[0] = texts[0].splitlines(True)
        with ignored(IndexError):
            texts[0][0] = sellCaps(texts[0][0])
        texts[0] = ''.join(texts[0])
        super(DictionaryEditor, self).prepare_texts(texts)
        with ignored(AttributeError):
            self.entry.parent.content = replace_datestamp(
                self.entry.parent.content)

    def _save_page(self):
        """Override method in SiteEditor"""
        super(DictionaryEditor, self)._save_page()
        self.serialise()

    @staticmethod
    def publish(entry, site, allpages=False):
        if entry.content:
            entry.publish(site.template)
        with ignored(AttributeError):
            entry.parent.publish(site.template)
        site.modify_source()
        site.update_json()

    def serialise(self):
        output = []
        transliteration = None
        language = None
        partofspeech = None
        for entry in map(lambda entry: self.linkadder.remove_links(remove_datestamp(entry.content)),
                         self.site):
            for line in entry.splitlines():
                if line.startswith('[1]'):
                    transliteration = line[len('[1]'):]
                elif line.startswith('[2]'):
                    language = line[len('[2]'):]
                elif line.startswith('[5]'):
                    line = re.sub(r'\[5\](.*?) <div class="definition">(.*?)</div>',
                                  r'\1\n\2', line)
                    try:
                        newpos, meaning = line.splitlines()
                    except:
                        continue
                    if newpos:
                        partofspeech = re.sub(r'\(.*?\)', '', newpos).split(' ')
                    definition = re.split(r'\W*', re.sub(r'<.*?>', '', meaning))
                    output.append(dict(
                        t=buyCaps(transliteration),
                        l=language,
                        p=partofspeech,
                        d=definition,
                        m=meaning
                    ))
        with open('c:/users/ryan/documents/tinellbianlanguages'
                        '/dictionary/wordlist.json', 'w') as f:
            json.dump(output, f, indent=2)

    def initial_content(self, entry=None):
        """
        Return the content to be placed in a textbox if the page is new
        """
        if entry is None:
            entry = self.entry
        name = entry.name
        tr = self.translator
        before = ('[1]{0}\n[2]{1}\n').format(name, tr.safename)
        before += '' if self.languagevar.get() == 'en' else '[3]{0}\n'.format(
            tr.convert_word(name))
        before += '[4][p {0}]/'.format(tr.code)
        after = '/[/p]\n[5]\n\n'
        return before + after

    @property
    def heading_commands(self):
        commands = super(DictionaryEditor, self).heading_commands
        commands += [(['<Control-r>'], self.refresh_random)]
        return commands


if __name__ == '__main__':
    links = [ExternalGrammar('c:/users/ryan/documents/'
                             'tinellbianlanguages/dictionarylinks.txt'),
             InternalDictionary()]
    app = DictionaryEditor(site=Dictionary(),
                           markdown=Markdown('c:/users/ryan/documents/'
                                             'tinellbianlanguages/dictionaryreplacements.mkd'),
                           links=AddRemoveLinks(links),
                           randomwords=RandomWords(20, 3))
    app.master.title('Dictionary Editor')
    app.mainloop()
