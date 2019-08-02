# -*- coding: utf-8 -*-
import codecs
import re
from evaluate import chars
import unicodedata
import glob
from evaluate.exceptions import (BadInput, FileNotFound)


def normalize_text(s):
    """Apply standard Unicode normalizations for OCR.
    This eliminates common ambiguities and weird unicode
    characters."""
    # s = s.decode('utf-8')
    s = unicodedata.normalize('NFC',s)
    s = re.sub(r'\s+(?u)', ' ', s)
    s = re.sub(r'\n(?u)', '', s)
    s = re.sub(r'^\s+(?u)', '', s)
    s = re.sub(r'\s+$(?u)', '', s)
    for m, r in chars.replacements:
        s = re.sub(m, r, s)
    return s


def project_text(s, kind="exact"):
    """Project text onto a smaller subset of characters
    for comparison."""
    s = normalize_text(s)
    s = re.sub(r'( *[.] *){4,}',u'....',s) # dot rows
    s = re.sub(r'[~_]',u'',s) # dot rows
    if kind == "exact":
        return s
    if kind == "nospace":
        return re.sub(r'\s','',s)
    if kind == "spletdig":
        return re.sub(r'[^A-Za-z0-9 ]', '', s)
    if kind == "letdig":
        return re.sub(r'[^A-Za-z0-9]', '', s)
    if kind == "letters":
        return re.sub(r'[^A-Za-z]', '', s)
    if kind == "digits":
        return re.sub(r'[^0-9]', '', s)
    if kind == "lnc":
        s = s.upper()
        return re.sub(r'[^A-Z]', '', s)
    raise BadInput("unknown normalization: "+kind)


def read_text(fname, nonl=1, normalize=1):
    """Read text. This assumes files are in unicode.
    By default, it removes newlines and normalizes the
    text for OCR processing with `normalize_text`"""
    with codecs.open(fname, "r", "utf-8") as stream:
        result = stream.read()
    if nonl and len(result) > 0 and result[-1] == '\n':
        result = result[:-1]
    if normalize:
        result = normalize_text(result)
    return result


##TODO: check
def allsplitext(path):
    """Split all the pathname extensions, so that "a/b.c.d" -> "a/b", ".c.d" """
    match = re.search(r'((.*/)*[^.]*)([^/]*)',path)
    if not match:
        return path, ""
    else:
        return match.group(1), match.group(3)


def glob_all(args):
    """Given a list of command line arguments, expand all of them with glob."""
    result = []
    for arg in args:
        if arg[0] == "@":
            with open(arg[1:], "r") as stream:
                expanded = stream.read().split("\n")
            expanded = [s for s in expanded if s != ""]
        else:
            expanded = sorted(glob.glob(arg))
        if len(expanded) < 1:
            raise FileNotFound("%s: expansion did not yield any files" % arg)
        result += expanded
    return result
