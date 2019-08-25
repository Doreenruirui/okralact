from __future__ import print_function

import warnings
import argparse
import sys
import os.path
from collections import Counter
import numpy as np

BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)

from evaluate import edist
from evaluate.prcoess_text import *
import multiprocessing

# disable rank warnings from polyfit
warnings.simplefilter('ignore', np.RankWarning)


class Args:
    def __init__(self):
        self.kind = 'exact'  #one from
        self.extension = '.txt'
        self.files = []
        self.confusion = 10
        self.context = 0
        self.parallel = multiprocessing.cpu_count()


def initializer(args, flag_word):
    global kind, extension, context, confusion, flag_word_err
    kind = args.kind
    extension = args.extension
    context = args.context
    confusion = args.confusion
    flag_word_err = flag_word


def process_confusion(fname):
    global kind, extension, context, confusion
    counts = Counter()
    gt = project_text(read_text(fname), kind=kind)
    ftxt = allsplitext(fname)[0] + extension
    if os.path.exists(ftxt):
        txt = project_text(read_text(ftxt), kind=kind)
    else:
        txt = ""
    # Also the ground truth cannot be empty, it is possible that
    # after filtering (args.kind) the gt string is empty.
    txt = unicodedata.normalize('NFC', txt)
    gt = unicodedata.normalize('NFC', gt)
    if len(gt) == 0:
        err = len(txt)
        if len(txt) > 0:
            cs = [(txt, '_' * len(txt))]
        else:
            cs = []
    else:
        err, cs = edist.xlevenshtein(txt, gt, context=context)
    for u, v in cs:
        counts[(u, v)] += 1
    return fname, err, len(gt), counts


def process_error_rate(fname):
    global kind, extension, flag_word_err
    gt = project_text(read_text(fname), kind=kind)
    ftxt = allsplitext(fname)[0] + extension
    if os.path.exists(ftxt):
        txt = project_text(read_text(ftxt), kind=kind)
    else:
        txt = ""
    txt = unicodedata.normalize('NFC', txt)
    gt = unicodedata.normalize('NFC', gt)
    if flag_word_err:
        txt = txt.split(' ')
        gt = gt.split(' ')
    # Also the ground truth cannot be empty, it is possible that
    # after filtering (args.kind) the gt string is empty.
    if len(gt) == 0:
        err = len(txt)
    else:
        err = edist.levenshtein(txt, gt)
    return fname, err, len(gt)


def evaluate_err_rate(files, flag_word=0, flag_confusion=0, extension='.txt'):
    args = Args()
    args.files = files
    args.extension = extension
    outputs = []
    if args.parallel < 2:
        initializer(args, flag_word=flag_word)
        for e in args.files:
            if flag_confusion:
                result = process_confusion(e)
            else:
                result = process_error_rate(e)
            outputs.append(result)
    else:
        try:
            pool = multiprocessing.Pool(args.parallel, initializer=initializer(args, flag_word=flag_word))
            if flag_confusion:
                for e in pool.imap_unordered(process_confusion, args.files, 10):
                    outputs.append(e)
            else:
                for e in pool.imap_unordered(process_error_rate, args.files, 10):
                    outputs.append(e)
        finally:
            pool.close()
            pool.join()
            del pool

    outputs = sorted(list(outputs))
    errs = 0
    total = 0
    if flag_confusion:
        counts = Counter()
        for fname, e, t, c in outputs:
            errs += e
            total += t
            counts += c
    else:
        for fname, e, t in outputs:
            errs += e
            total += t
    res = {}
    res["total"] = int(total)
    res["errs"] = int(errs)
    res["err_rate"] = errs * 1.0 / total
    if  flag_confusion:
        res['confusion'] = []
        for (a, b), v in counts.most_common(args.confusion):
            print("%d\t%s\t%s" % (v, a, b))
            res['confusion'].append((v, a, b))
    return  res

def evaluate(files, flag_confusion, extension='.txt'):
    char_res = evaluate_err_rate(files, flag_word=0, flag_confusion=flag_confusion, extension=extension)
    word_res = evaluate_err_rate(files,  flag_word=1, flag_confusion=0, extension=extension)
    res = {}
    res["char_total"] =  char_res["total"]
    res["char_errs"] = char_res["errs"]
    res["char_error_rate"] = char_res["err_rate"]
    if flag_confusion:
        res["confusion"] =  char_res["confusion"]
    res["word_total"] =  word_res["total"]
    res["word_errs"] = word_res["errs"]
    res["word_error_rate"] = word_res["err_rate"]
    return res
