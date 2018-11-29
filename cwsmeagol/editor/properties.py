import sys
import os
import json
import re
from addremovelinks import AddRemoveLinks
from cwsmeagol.site.site import Site
from cwsmeagol.translation import *
from cwsmeagol.utils import *
from cwsmeagol.defaults import default
import tkFileDialog as fd
import tkSimpleDialog as sd

class Properties(object):
    def __init__(self, config=None, caller=None):
        super(Properties, self).__init__()
        self.caller = caller
        self.setup(config)

    def setup(self, config):
        self.config_filename = config
        try:
            with open(self.config_filename) as config:
                self.config = json.load(config)
        except (IOError, TypeError):
            self.config = json.loads(default.config)
        self.create_site()
        self.create_linkadder()
        self.translator = Translator(self.language)
        self.evolver = HighToVulgarLulani()
        self.randomwords = RandomWords(self.language)
        self.markdown = Markdown(self.markdown_file)

    def __getattr__(self, attr):
        if attr in {'files', 'source', 'destination', 'template',
                'template_file', 'name', 'searchindex'}:
            return getattr(self.site, attr)
        elif attr in {'page', 'language', 'position', 'fontsize'}:
            return self.config['current'][attr]
        elif attr is 'markdown_file':
            return self.config['current']['markdown']
        elif attr is 'links':
            return self.config['links']
        elif attr is 'site_info':
            return self.config['site']
        else:
            return getattr(super(Properties, self), attr)

    def __setattr__(self, attr, value):
        if attr in {'page', 'language', 'position', 'fontsize'}:
            self.config['current'][attr] = value
        elif attr == 'markdown_file':
            self.config['current']['markdown'] = value
        elif attr == 'markdown':
            self.set_markdown(attr, value)
        elif attr in {'name', 'destination'}:
            self.config['site'][attr] = value
        elif attr == 'links':
            self.config['links'] = value
        else:
            super(Properties, self).__setattr__(attr, value)

    def set_markdown(self, attr, value):
        try:
            super(Properties, self).__setattr__(attr, Markdown(value))
        except TypeError: # value is already a Markdown instance
            super(Properties, self).__setattr__(attr, value)

    def collate(self):
        self.name = self.site.name
        self.destination = self.site.destination
        self.links = self.linkadder.adders

    def open_site(self):
        filetypes = [('Sm\xe9agol File', '*.smg'), ('Source Data File', '*.txt')]
        title = 'Open Site'
        filename = fd.askopenfilename(filetypes=filetypes, title=title)
        if filename and filename.endswith('.smg'):
            self.setup(filename)
            return False
        return filename

    def save_site(self, filename=None):
        self.page = list(self.heading_contents)
        self.config_filename = filename or self.config_filename
        self.collate()
        if self.config_filename:
            with ignored(IOError):
                with open(self.config_filename, 'w') as config:
                    json.dump(self.config, config, indent=2)
                folder = os.getenv('LOCALAPPDATA')
                inifolder = os.path.join(folder, 'smeagol')
                inifile = os.path.join(inifolder, self.caller + '.ini')
                with ignored(os.error): # folder already exists
                    os.makedirs(inifolder)
                with open(inifile, 'a') as inisave:
                    pass    # ensure file exists
                try:
                    with open(inifile, 'r') as inisave:
                        sites = json.load(inisave)
                except ValueError:
                    sites = dict()
                with open(inifile, 'w') as inisave:
                    name = re.match(
                            r'.*/(.*?)\.',
                            self.config_filename
                        ).group(1).capitalize()
                    sites[name] = self.config_filename
                    json.dump(sites, inisave, indent=2)
                return # successful save
        self.save_site_as() # unsuccessful save

    def save_site_as(self):
        filetypes = [('Sm\xe9agol File', '*.smg')]
        title = 'Save Site'
        filename = fd.asksaveasfilename(filetypes=filetypes, title=title)
        if filename:
            filename = re.sub(r'(\.smg)?$', r'.smg', filename)
            self.config_filename = filename
            self.save_site()

    def create_site(self):
        self.site = Site(**self.site_info)

    def create_linkadder(self):
        self.linkadder = AddRemoveLinks(self.links)

    def update(self, properties):
        property = properties['property']
        owner = properties['owner']
        value = properties.get('value')
        checked = properties.get('checked')
        if owner == 'links':
            if checked:
                self.linkadder += {property: value}
            else:
                self.linkadder -= {property: value}
        else:
            setattr(self.site, property, value)
