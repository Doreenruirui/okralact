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
        self.allconf = None
        self.perfile = None
        self.context = 0
        self.parallel = multiprocessing.cpu_count()


def initializer(args):
    global kind, extension, context, confusion, allconf
    kind = args.kind
    extension = args.extension
    context = args.context
    confusion = args.confusion
    allconf = args.allconf


def process1(fname):
    global kind, extension, context, confusion, allconf
    counts = Counter()
    gt = project_text(read_text(fname), kind=kind)
    ftxt = allsplitext(fname)[0] + extension
    missing = 0
    if os.path.exists(ftxt):
        txt = project_text(read_text(ftxt), kind=kind)
    else:
        missing = len(gt)
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
    if confusion > 0 or allconf is not None:
        for u, v in cs:
            counts[(u, v)] += 1
    return fname, err, len(gt), missing, counts


def process2(fname):
    global kind, extension, allconf
    gt = project_text(read_text(fname), kind=kind)
    ftxt = allsplitext(fname)[0] + extension
    missing = 0
    if os.path.exists(ftxt):
        txt = project_text(read_text(ftxt), kind=kind)
    else:
        missing = len(gt)
        txt = ""

    txt = unicodedata.normalize('NFC', txt).split(' ')
    gt = unicodedata.normalize('NFC', gt).split(' ')
    # Also the ground truth cannot be empty, it is possible that
    # after filtering (args.kind) the gt string is empty.
    if len(gt) == 0:
        err = len(txt)
    else:
        err = edist.levenshtein_word(txt, gt)
    return fname, err, len(gt), missing


def evaluate(files):
    args = Args()
    args.files = files
    outputs = []
    outputs_wer = []
    if args.parallel < 2:
        initializer(args)
        for e in args.files:
            result = process1(e)
            outputs.append(result)
            result_wer = process2(e)
            outputs_wer.append(result_wer)
    else:
        try:
            pool = multiprocessing.Pool(args.parallel, initializer=initializer(args))
            for e in pool.imap_unordered(process1, args.files, 10):
                outputs.append(e)
        finally:
            pool.close()
            pool.join()
            del pool
        try:
            pool1 = multiprocessing.Pool(args.parallel, initializer=initializer(args))
            for e in pool1.imap_unordered(process2, args.files, 10):
                outputs_wer.append(e)
        finally:
            pool1.close()
            pool1.join()
            del pool1
    outputs = sorted(list(outputs))
    outputs_wer = sorted(list(outputs_wer))

    perfile = None
    if args.perfile is not None:
        perfile = codecs.open(args.perfile, "w", "utf-8")
    allconf = None
    if args.allconf is not None:
        allconf = codecs.open(args.allconf, "w", "utf-8")
    errs = 0
    total = 0
    missing = 0
    counts = Counter()
    for fname, e, t, m, c in outputs:
        errs += e
        total += t
        missing += m
        counts += c
        if perfile is not None:
            perfile.write("%6d\t%6d\t%s\n" % (e, t, fname))
        if allconf is not None:
            for (a, b), v in c.most_common(1000):
                allconf.write("%s\t%s\t%s\n" % (a, b, fname))
    errs_w = 0
    total_w = 0
    missing_w = 0
    for fname, e, t, m in outputs_wer:
        errs_w += e
        total_w += t
        missing_w += m

    if perfile is not None:
        perfile.close()
    if allconf is not None:
        allconf.close()

    res = {}
    res['errors'] = int(errs)
    res['missing'] = int(missing)
    res['total'] = int(total)
    res['errors_word'] = int(errs)
    res['missing_word'] = int(missing)
    res['total_word'] = int(total)
    if total > 0:
        res['char_error_rate'] = "%.3f " % (errs * 1.0 / total)
        res['errnomiss'] = "%8.3f " % ((errs-missing) * 100.0 / total)
        res['word_error_rate'] = "%.3f " % (errs_w * 1.0 / total_w)
    # if args.confusion > 0:
    #     res['confusion'] = []
    #     for (a, b), v in counts.most_common(args.confusion):
    #         print("%d\t%s\t%s" % (v, a, b))
    #         res['confusion'].append((v, a, b))
    print(res)
    return res
