#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""This script parses an Anki collection consisting of multilingual vocabulary
notes.

All notes have a model 'multilingual', i.e. they have 5 fields corresponding to
one language.

* FR: French
* EN: English
* UK: British
* US: American
* ES: Spanish
* AL: Latin america

Fields can be empty, except the field FR.

The objective of this script is to format the notes according to this model.
Initially, notes can have one of the following entries in the FR field:

* FR: WORD ; these notes are correctly formatted and the translation is set in
  set in the right field.
* FR: WORD (EN / ES) ; these notes have the translation for each language set
in the fielt EN.
* FR: WORD (EN / ES) (2 / 3) ; idem as above, with in addition the number of
words for each language.

"""
import sys
import re
import logging
logging.basicConfig(format=u'%(levelname)s:%(message)s', level=logging.DEBUG)
sys.path.append('/usr/share/anki')
from anki import Collection

LANGS = ['EN', 'ES', 'US', 'UK', 'AL']


def format_text(text):
    text = text.replace('&nbsp;', ' ')
    text = re.sub('<[^>]+>', '', text)
    text = re.sub('<br />', '', text)
    text = text.strip()
    return text


def parse_FR(text):
    """From the field FR, return the languages and format the text.

    Parameters
    ----------
    text : str
        Text in the field.

    Returns
    -------
    list of str
        List of languages.
    str
        Word without language info.

    Examples
    --------
    >>> parse_FR('un mot')
    ([], 'un mot')
    >>> parse_FR('un mot (3)')
    ([], 'un mot')
    >>> parse_FR('un mot (EN / ES)')
    (['EN', 'ES'], 'un mot')
    >>> parse_FR('un mot (EN / UK / US) (3 / 3 / 3)')
    (['EN', 'UK', 'US'], 'un mot')
    >>> parse_FR('un <span>mot<\span> (EN&nbsp;/ UK / US) (3 / 3 / 3) <br />')
    (['EN', 'UK', 'US'], 'un mot')
    """
    PATTERN_LANG = '|'.join(LANGS)
    PATTERN_LANG_FULL = '\((?:(?:{0})+\s/\s)+(?:{0})+\)'.format(PATTERN_LANG)
    PATTERN_OCC_FULL = '\((?:\d)(?:\s/\s\d)*\)'

    # format text
    text = format_text(text)

    # find and remove lang pattern
    langs = re.findall('|'.join(LANGS), text)

    if langs:
        # remove langs and count
        text = re.sub(PATTERN_LANG_FULL, '', text)

    text = re.sub(PATTERN_OCC_FULL, '', text)
    text = format_text(text)

    return langs, text


def parse_EN(text, langs):
    """From the field EN, get words in all languages.

    Parameters
    ----------
    text : str
        Text in the field.
    langs : list of str
        List of languages.

    Returns
    -------
    list
        List of formatted words in corresponding languages.

    Examples
    --------
    >>> parse_EN('a word / una palabra', ['EN', 'ES'])
    ['a word', 'una palabra']
    >>> parse_EN('<span>a word<\span> / una&nbsp;palabra', ['EN', 'ES'])
    ['a word', 'una palabra']
    """
    text = format_text(text)
    words = [format_text(word) for word in text.split('/')]
    return words


def main():

    collection_path = "collection.anki2"
    collection = Collection(collection_path)

    # get ordering of languages in the model
    ord_lang = {field['name']: field['ord']
                for field in collection.models.all()[1]['flds']}

    for note_id in collection.findNotes('*'):

        note = collection.getNote(note_id)
        langs, word_fr = parse_FR(note.fields[ord_lang['FR']])

        note.fields[ord_lang['FR']] = word_fr

        if langs:
            words = parse_EN(note.fields[ord_lang['EN']], langs)
            if len(words) == len(langs):
                for idl, lang in enumerate(langs):
                    note.fields[ord_lang[lang]] = words[idl]
                logging.info('Updated %s', word_fr)
            else:
                logging.error('Error with note %s', str(note.fields))
        else:
            logging.debug('Not updated: %s', note.fields[ord_lang['FR']])
        note.flush()

    collection.close()


if __name__ == '__main__':
    main()
