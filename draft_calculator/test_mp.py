#!/usr/bin/env python

from multiprocessing import Pool

def f(msg, x):
    print msg, x
    return [y*y for y in x]

def main():
    msg = 'calling with'

    def _f(x):
        return f(msg, x)

    pool = Pool()
    x = pool.imap_unordered(_f, [[1,2,3],[4,5,6]])
    for y in x:
        print y

main()
