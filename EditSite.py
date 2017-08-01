import Tkinter as Tk
import os
import thread
from Smeagol import *
from Translation import *
from Edit import *


class EditPage(Edit):
    def __init__(self, directories, datafiles, sites, markdowns, master=None):
        widgets = Widgets(3, 1, 2)
        Edit.__init__(self, 'grammar', directories, datafiles, sites, markdowns, widgets)
        self.sitename = Tk.StringVar()
        self.sitename.set('grammar')
        self.datafiles = datafiles
        self.datafile = self.choose(self.sitename.get(), datafiles)
        self.sites = sites
        self.site = self.choose(self.sitename.get(), sites)
        self.markdowns = markdowns
        self.markdown = self.choose(self.sitename.get(), markdowns)
        self.directories = directories
        os.chdir(self.choose(self.sitename.get(), directories))
        self.number_of_words = Tk.StringVar()
        self.number_of_words.set('')
        self.entry = self.site.root
        self.configure_widgets()

    def configure_widgets(self):
        for i, heading in enumerate(self.headings):

            def handler(event, self=self, i=i):
                return self.scroll_headings(event, i)
            heading.bind('<Prior>', handler)
            heading.bind('<Next>', handler)
        self.headings[0].bind('<Return>', self.insert_chapter)
        self.headings[1].bind('<Return>', self.insert_heading)
        self.headings[2].bind('<Return>', self.load)
        self.textboxes[0].bind('<KeyPress>', self.textbox_changed)
        self.textboxes[0].bind('<Control-BackSpace>', self.backspace_word)
        self.textboxes[0].bind('<Control-Delete>', self.delete_word)
        self.textboxes[0].bind('<Control-a>', self.select_all)
        self.textboxes[0].bind('<Control-m>', self.refresh_markdown)
        self.textboxes[0].bind('<Control-o>', self.refresh_site)
        self.textboxes[0].bind('<Control-r>', self.load)
        self.textboxes[0].bind('<Control-s>', self.save)
        self.textboxes[0].bind('<Control-t>', self.table)
        self.textboxes[0].bind('<Shift-Tab>', self.go_to_heading)
        self.textboxes[0].configure(font=('Corbel', '14'))
        self.infolabel.configure(textvariable=self.number_of_words)
        self.radios[0].configure(text='Grammar', variable=self.sitename, value='grammar', command=self.change_site)
        self.radios[1].configure(text='Story', variable=self.sitename, value='story', command=self.change_site)
        self.radios[0].select()
        self.headings[0].focus_set()

    def go_to_heading(self, event=None):
        self.headings[2].focus_set()
        return 'break'

    def refresh_site(self, event=None):
        self.site.refresh()
        self.load()
        self.number_of_words.set('Site Refreshed!')

    def refresh_markdown(self, event=None):
        """
        Re-open replacements page.
        """
        self.markdown.refresh()
        self.number_of_words.set('Markdown Refreshed!')
        return 'break'

    def scroll_headings(self, event, level):
        """
        Respond to PageUp / PageDown by changing headings, moving through the hierarchy.
        :param event (Event): which entry box received the KeyPress
        :param level (int): the level of the hierarchy that is being traversed.
        """
        heading = self.headings[level]
        # bring
        level += 1
        direction = 1 if event.keysym == 'Next' else -1
        # traverse hierarchy sideways
        if self.entry.level == level:
            try:
                self.entry = self.entry.sister(direction)
            except IndexError:
                pass
        # ascend hierarchy until correct level
        while self.entry.level > level:
            try:
                self.entry = self.entry.parent
            except AttributeError:
                break
        # descend hierarchy until correct level
        while self.entry.level < level:
            try:
                self.entry = self.entry.children[0]
            except IndexError:
                break
        for k in range(level - 1, 3):
            self.headings[k].delete(0, Tk.END)
        heading.insert(Tk.INSERT, self.entry.name)
        return 'break'

    def select_all(self, event=None):
        self.textboxes[0].tag_add('sel', '1.0', 'end')
        return 'break'

    def change_site(self, event=None):
        site = self.sitename.get()
        if self.site is None or site != self.sitename:
            for heading in self.headings:
                heading.delete(0, Tk.END)
            self.textboxes[0].delete(1.0, Tk.END)
            os.chdir(self.choose(site, self.directories))
            self.datafile = self.choose(site, self.datafiles)
            self.site = self.choose(site, self.sites)
            self.markdown = self.choose(site, self.markdowns)
            self.entry = self.site.root
            self.headings[0].focus_set()
        return 'break'

    def table(self, event=None):
        """
        Insert markdown for table, and place insertion point between them.
        """
        self.textboxes[0].insert(Tk.INSERT, '[t]\n[/t]')
        self.textboxes[0].mark_set(Tk.INSERT, Tk.INSERT + '-5c')
        return 'break'

    def insert_chapter(self, event):
        self.headings[1].focus_set()
        return 'break'

    def insert_heading(self, event=None):
        self.headings[2].focus_set()
        return 'break'

    def delete_word(self, event=None):
        if self.textboxes[0].get(Tk.INSERT + '-1c') in ' .,;:?!':
            self.textboxes[0].delete(Tk.INSERT, Tk.INSERT + ' wordend +1c')
        elif self.textboxes[0].get(Tk.INSERT) == ' ':
            self.textboxes[0].delete(Tk.INSERT, Tk.INSERT + '+1c wordend')
        elif self.textboxes[0].get(Tk.INSERT) in '.,;:?!':
            self.textboxes[0].delete(Tk.INSERT, Tk.INSERT + '+1c')
        else:
            self.textboxes[0].delete(Tk.INSERT, Tk.INSERT + ' wordend')
        self.update_wordcount()
        return 'break'

    def backspace_word(self, event=None):
        if self.textboxes[0].get(Tk.INSERT + '-1c') in '.,;:?!':
            self.textboxes[0].delete(Tk.INSERT + '-1c wordstart', Tk.INSERT)
        elif self.textboxes[0].get(Tk.INSERT + '-1c') in ' ':
            self.textboxes[0].delete(Tk.INSERT + '-2c wordstart', Tk.INSERT)
        else:
            self.textboxes[0].delete(Tk.INSERT + '-1c wordstart', Tk.INSERT)
        self.update_wordcount()
        return 'break'

    def update_wordcount(self, event=None):
        text = self.textboxes[0].get(1.0, Tk.END)
        self.number_of_words.set(str(text.count(' ') + text.count('\n')))

    def textbox_changed(self, event=None):
        self.update_wordcount()
        if self.textboxes[0].edit_modified():
            self.save_text.set('*Save')

    def load(self, event=None):
        # descend hierarchy in correct direction
        self.entry = self.site
        for heading in self.headings:
            try:
                self.entry = self.entry[heading.get()]
            except KeyError:
                pass
        self.textboxes[0].delete(1.0, Tk.END)
        if self.entry is not self.site:
            entry = re.sub('<a href="http://dictionary.tinellb.com/.*?">(.*?)</a>',
                                        r'<link>\1</link>', self.entry.content)
            entry = self.markdown.to_markdown(entry)
            self.textboxes[0].insert(1.0, entry)
            self.textboxes[0].focus_set()
            self.textboxes[0].edit_modified(False)
            self.save_text.set('Save')
        else:
            self.entry = self.site.root
            self.textboxes[0].insert(1.0, 'That page does not exist. Create a new page by appending to an old one.')
            self.headings[1].focus_set()
        self.update_wordcount()
        return 'break'

    def save(self, event=None):
        self.save_text.set('Save')
        self.update_wordcount()
        self.entry.content = self.markdown.to_markup(str(self.textboxes[0].get(1.0, Tk.END)))
        while self.entry.content[-2:] == '\n\n':
            self.entry.content = self.entry.content[:-1]
        # remove duplicate linebreaks
        self.entry.content = re.sub(r'\n\n+', '\n', self.entry.content)
        # update datestamp and publish.
        self.entry.content = self.markdown.to_markup(self.markdown.to_markdown(self.entry.content))
        if self.entry.content == '\n':
            self.entry.delete()
            self.entry.remove()
        else:
            self.replace_links()
            self.entry.publish(self.site.template)
        entry = str(self.site)
        if entry:
            with open(self.datafile, 'w') as data:
                data.write(str(self.site))
        self.site.update_json()
        self.textboxes[0].edit_modified(False)
        return 'break'

    def replace_links(self):
        """
        Replaces appropriate words in text with links to dictionary.tinellb.com.
        :precondition: text is a grammar page with text in Smeagol markup.
        """
        links = set(re.sub(r'.*?<link>(.*?)</link>.*?', r'\1@', self.entry.content.replace('\n', '')).split(r'@')[:-1])
        matriarch = self.entry.ancestors()[1].urlform
        for link in links:
            url = Page(link, markdown=self.site.markdown).urlform
            initial = re.sub(r'.*?(\w).*', r'\1', url)
            try:
                self.entry.content = self.entry.content.replace('<link>' + link + '</link>',
                '<a href="http://dictionary.tinellb.com/' + initial + '/' + url + '.html#' + matriarch + '">' + link + '</a>')
            except KeyError:
                pass

app = EditPage(directories={'grammar': 'c:/users/ryan/documents/tinellbianlanguages/grammar',
                            'story': 'c:/users/ryan/documents/tinellbianlanguages/thecoelacanthquartet'},
                    datafiles='data.txt',
                    sites={'grammar': Grammar(), 'story': Story()},
                    markdowns=Markdown('c:/users/ryan/documents/tinellbianlanguages/grammarstoryreplacements.html'))
app.master.title('Edit Page')
app.mainloop()
