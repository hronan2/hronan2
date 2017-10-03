# -*- coding: utf-8 -*-
#!/usr/bin/python2
"""This script parses an Anki collection consisting of multilingual vocabulary
notes.

All notes are of type 'multilingual', i.e. they have one field for each
language.

After import, the first field gives the languages of the word of the second
fields, that are separated by a slash:

    Field 1: WORD (EN / ES)
    Field 2: WORD IN ES / WORD IN ES
    Field 3: Empty

If no language is given, the notes are already well-formatted.
"""
import sys
import re
sys.path.append('/usr/share/anki')
from anki import Collection

LANGS = ['EN', 'ES', 'US', 'UK', 'AL']

collection_path = "collection.anki2"
collection = Collection(collection_path)

note_ids = collection.findNotes('*')
ord_lang = {field['name']: field['ord']
          for field in collection.models.all()[1]['flds']}


def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    text = TAG_RE.sub('', text)
    text = text.replace('<br />', '')
    return text


def format_word(word):
    word = word.replace('&nbsp;', '')
    word = word.strip()
    return word


def parse_FR(field):
    """From the field FR (initially front card) and return the languages."""
    field = remove_tags(field)
    langs = re.findall('|'.join(LANGS), field)
    word = field.replace('({})'.format(' / '.join(langs)), '')
    return langs, word


def parse_EN(field, langs):
    """From the field EN (initially back card) and get the words."""
    field = remove_tags(field)
    words = field.split('/')
    if len(words) != len(langs):
        return None
    else:
        return [format_word(word) for word in words]


for note_id in note_ids:

    note = collection.getNote(note_id)
    langs, word_fr = parse_FR(note.fields[ord_lang['FR']])

    if langs:
        words = parse_EN(note.fields[ord_lang['EN']], langs)

        if words is not None:
            note.fields[ord_lang['FR']] = word_fr
            for idl, lang in enumerate(langs):
                note.fields[ord_lang[lang]] = words[idl]
            note.flush()
            print('CHANGED: ', note.fields[ord_lang['FR']])
        else:
            print('ERROR: ', note.fields)
    else:
        print('NOT CHANGED: ', note.fields[ord_lang['FR']])

collection.close()
