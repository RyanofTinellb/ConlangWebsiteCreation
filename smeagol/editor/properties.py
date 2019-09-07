import sys
import os
import json
import re
from .addremovelinks import AddRemoveLinks
from .templates_window import TemplatesWindow
from .properties_window import PropertiesWindow
from ..site.site import Site
from ..translation import *
from ..utils import *
from ..defaults import default
import tkinter.filedialog as fd
import tkinter.simpledialog as sd


class Properties:
    def __init__(self, config=None, caller=None, master=None):
        self.setup(config)
        try:
            super().__init__(master)
        except TypeError: # Properties being used without a master
            super().__init__()

    def setup(self, filename, source=False):
        if source: # filename refers to a .src file
            self.configuration = json.loads(default.config)
            self.source = filename
        else: # filename refers to a .smg file
            self.config_filename = filename
            try:
                with open(self.config_filename, encoding='utf-8') as config:
                    self.configuration = json.load(config)
            except (IOError, TypeError):
                self.configuration = json.loads(default.config)
        self.setup_site()
        self.linkadder = AddRemoveLinks(self.links, self.wordlist, self.translator)
        self.marker = Markdown(self.markdown_file)

    def setup_linguistics(self):
        # override Editor.setup_linguistics()
        self.evolver = HighToDemoticLulani()
        self.randomwords = RandomWords(self.language, self.sample_texts)
        self.setup_markdown()

    def setup_site(self):
        while True:
            try:
                self.site = Site(**self.site_info)
                break
            except SourceFileNotFoundError:
                filetypes = [('Source Data File', '*.src')]
                title = 'Open Source'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.source = filename
            except TemplateFileNotFoundError:
                filetypes = [('HTML Template', '*.html')]
                title = 'Open Template'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.template_file = filename
            except WholepageTemplateFileNotFoundError:
                filetypes = [('Wholepage Template', '*.html')]
                title = 'Open Template'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.wholepage_template = filename
            except SearchTemplateFileNotFoundError:
                filetypes = [('Search Page Template', '*.html')]
                title = 'Open Template for Search Page'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.search_template = filename
            except Search404TemplateFileNotFoundError:
                filetypes = [('404 Page Template', '*.html')]
                title = 'Open Template for 404 Page'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.search_template404 = filename

    def setup_markdown(self, filename=None):
        self.markdown_file = filename or self.markdown_file
        while True:
            try:
                self.marker = Markdown(self.markdown_file)
                break
            except MarkdownFileNotFoundError:
                filetypes = [('Markdown File', '*.mkd')]
                title = 'Open Markdown file'
                filename = fd.askopenfilename(filetypes=filetypes, title=title,
                    defaultextension=filetypes[0][1][1:])
                self.markdown_file = filename

    def __getattr__(self, attr):
        if attr in {'language', 'fontsize'}:
            return self.configuration['current'][attr]
        elif attr == 'site':
            return None
        elif attr == 'markdown_file':
            return self.configuration['current']['markdown']
        elif attr in {'markdown', 'markup'}:
            return getattr(self.marker, f'to_{attr}')
        elif attr in {'remove_links', 'add_links'}:
            return getattr(self.linkadder, attr)
        elif attr == 'links':
            return self.configuration[attr]
        elif attr == 'sample_texts':
            return self.configuration.get('sample texts', '')
        elif attr == 'site_info':
            return self.configuration['site']
        elif attr == 'translator':
            return Translator(self.language)
        elif attr == 'history':
            return self.get_history()
        elif attr == 'page':
            return self.get_page()
        elif attr == 'sections':
            sections = getattr(self.site, attr)
            self.configuration['sections'] = sections
            return sections
        else:
            try:
                return getattr(self.site, attr)
            except AttributeError:
                return getattr(super(), attr)

    def __setattr__(self, attr, value):
        if attr in {'language', 'fontsize'}:
            self.configuration['current'][attr] = value
        elif attr == 'markdown_file':
            self.configuration['current']['markdown'] = value
        elif attr == 'marker':
            self.set_markdown(attr, value)
        elif attr in {'name', 'destination'}:
            self.configuration['site'][attr] = value
        elif attr in {'source', 'template_file'}:
            self.configuration['site']['files'][attr] = value
        elif attr in {'links', 'history'}:
            self.configuration[attr] = value
        elif attr == 'sample_texts':
            self.configuration['randomwords']
        elif attr == 'page':
            self.history.replace(value)
        else:
            try:
                setattr(self.site, attr, value)
                self.configuration['files'] = self.site.files
            except AttributeError:
                super().__setattr__(attr, value)

    def set_markdown(self, attr, value):
        try:
            super(Properties, self).__setattr__(attr, Markdown(value))
        except TypeError: # value is already a Markdown instance
            super(Properties, self).__setattr__(attr, value)

    def get_history(self):
        history = self.configuration.get('history', [])
        if isinstance(history, ShortList):
            return history
        else:
            self.history = ShortList(history, 20)
            return self.history

    def get_page(self):
        try:
            return self.history[-1]
        except IndexError:
            return []

    def collate_config(self):
        self.name = self.site.name
        self.destination = self.site.destination
        self.links = self.linkadder.adders

    def open_site(self):
        filetypes = [('Sméagol File', '*.smg'), ('Source Data File', '*.src')]
        title = 'Open Site'
        filename = fd.askopenfilename(filetypes=filetypes, title=title,
            defaultextension='.smg')
        if filename:
            self.setup(filename, source=filename.endswith('.src'))

    def save_site(self, filename=None):
        self.config_filename = filename or self.config_filename
        self.collate_config()
        if self.config_filename:
            with ignored(IOError):
                with open(self.config_filename, 'w', encoding='utf-8') as config:
                    json.dump(self.configuration, config, indent=2)
                folder = os.getenv('LOCALAPPDATA')
                inifolder = os.path.join(folder, '.')
                inifile = os.path.join(inifolder, self.caller + '.ini')
                with ignored(os.error): # folder already exists
                    os.makedirs(inifolder)
                with open(inifile, 'a', encoding='utf-8') as inisave:
                    pass    # ensure file exists
                try:
                    with open(inifile, 'r', encoding='utf-8') as inisave:
                        sites = json.load(inisave)
                except ValueError:
                    sites = dict()
                with open(inifile, 'w', encoding='utf-8') as inisave:
                    name = re.match(
                            r'.*/(.*?)\.',
                            self.config_filename
                        ).group(1).capitalize()
                    sites[name] = self.config_filename
                    json.dump(sites, inisave, indent=2)
                return # successful save
        self.save_site_as() # unsuccessful save

    def save_site_as(self):
        filetypes = [('Sméagol File', '*.smg')]
        title = 'Save Site'
        filename = fd.asksaveasfilename(filetypes=filetypes, title=title,
                                        defaultextension='.smg')
        if filename:
            self.config_filename = filename
            self.save_site()

    def update(self, properties):
        try:
            property = properties['property']
        except KeyError:
            return
        owner = properties['owner']
        value = properties.get('value')
        checked = properties.get('checked')
        if owner == 'links':
            if checked:
                self.linkadder += {property: value}
            else:
                self.linkadder -= {property: value}
        elif owner == 'random words':
            setattr(self.randomwords, property, value)
            if self.randomwords.name == 'English':
                self.randomwords.select()
        else:
            setattr(self.site, property, value)

    @property
    def all_templates(self):
        templates = [
            dict(use_name='Main', filename=self.template_file),
            dict(use_name='Wholepage', filename=self.wholepage_template),
            dict(use_name='Search', filename=self.search_template),
            dict(use_name='404', filename=self.search_template404)]
        for template in templates:
            template['enabled'] = False
        for use_name, filename in self.sections.items():
            templates += [dict(use_name=use_name, filename=filename,
                               enabled=True)]
        return templates

    def edit_templates(self, event=None):
        while True:
            window = TemplatesWindow(self.all_templates, self.edit_file)
            self.wait_window(window)
            templates = {
                'Main': 'template_file',
                'Wholepage': 'wholepage_template',
                'Search': 'search_template',
                '404': 'search_template404'}
            for template in window.get():
                if template['enabled']:
                    self.sections[template['use_name']] = template['filename']
                else:
                    attr = templates[template['use_name']]
                    value = template['filename']
                    setattr(self, attr, value)
            try:
                self.setup_templates()
                message = 'Do you wish to apply these templates to all pages?'
                if mb.askyesno('Publish All', message):
                    self.site_publish()
                self.textbox.focus_set()
                break
            except KeyError as err:
                name = str(err)[1:-1]
                self.sections[name] = ''

    def site_properties(self, event=None):
        properties_window = PropertiesWindow(self)
        self.wait_window(properties_window)
        self.site.root.name = self.site.name
        self.save_site()