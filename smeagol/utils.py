import functools
import json
import os
import re
import tkinter as Tk
from contextlib import contextmanager
from datetime import datetime as dt
from threading import Thread

from . import errors


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def tkinter():
    def decorator(function):
        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            self._to_html()
            value = function(self, *args, **kwargs)
            self._from_html()
            return value
        return wrapper
    return decorator


def timeit(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        oldtime = dt.now()
        value = function(*args, **kwargs)
        newtime = dt.now()
        print(('Done: ' + str(newtime - oldtime)))
        return value
    return wrapper


def asynca(function):
    @functools.wraps(function)
    def async_function(*args, **kwargs):
        thread = Thread(target=function, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return async_function


def display_attrs(obj):
    for attr in dir(obj):
        value = getattr(obj, attr)
        print(attr, type(value), value)
        print()


def clear_screen():
    os.system('cls')


def increment(lst, by):
    lst = [x + by for x in lst]
    return lst


def stringify(obj, indent=0):
    output = ''
    if isinstance(obj, dict):
        for k, v in obj.items():
            output += f'{indent * "-"}{k} - {stringify(v, indent+2)}'
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for v in obj:
            output += f'{indent * "-"}{stringify(v, indent+2)}'
    else:
        output += f'{indent * "-"}{obj}'
    return output


def save(obj, filename):
    try:
        saves(json.dumps(obj, ensure_ascii=False, indent=2), filename)
    except TypeError:
        saves(str(obj), f := filename + '!error.txt')
        print(f)
        raise


def saves(string, filename):
    with ignored(os.error):
        os.makedirs(os.path.dirname(filename))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(string)


def load(filename):
    with open(filename, encoding='utf-8') as f:
        return json.load(f)


def loads(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()


def update(filename, fn):
    '''
    Run function `fn` on object `obj` in `filename`
    '''
    obj = load(filename)
    fn(obj)
    save(obj, filename)


def updates(filename, fn):
    saves(fn(loads(filename)), filename)


def buyCaps(word):
    return re.sub(r'[$](.)', _buy, word).replace('.', '&nbsp;')


def _buy(regex):
    return regex.group(1).capitalize()


def sellCaps(word):
    return re.sub(r'(.)', _sell, word.replace(' ', '.'))


def _sell(regex):
    letter = regex.group(1)
    if letter != letter.lower():
        return '$' + letter.lower()
    else:
        return letter


def change_text(item, replacement, text):
    try:
        text[0] = re.sub(item, replacement, text[0])
    except FutureWarning:
        print(item)
    return text


Tk.FIRST = 0
Tk.LAST = Tk.END
Tk.ALL = (Tk.FIRST, Tk.LAST)


def Tk_compare(tb, first, op, second):
    try:
        return tb.compare(first, op, second)
    except Tk.TclError:
        return tb.compare(Tk.INSERT, op, second)


def remove_text(item, text):
    return change_text(item, '', text)


def un_url(text, markdown=None):
    text = text.replace(' ', '.')
    if markdown:
        text = markdown.to_markup(text)
    return sellCaps(text)


def urlform(text):
    name = text.lower()
    # remove tags, text within tags, and spaces
    name = re.sub(r'(<(div|ipa).*?\2>)|<.*?>| ', '', name)
    return name


def page_initial(name, markdown=None):
    '''Returns the first letter of a word, i.e.: the folder of the Dictionary
        in which that word would appear
        @error: IndexError if the text only contains punctuation'''
    if markdown:
        name = markdown.to_markdown(name)
    return re.findall(r'\w', name)[0]
