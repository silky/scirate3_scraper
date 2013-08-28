#!/usr/bin/env python
# coding: utf-8

import re, os, sys, pdb, datetime

import codecs, unicodedata

from collections import defaultdict

from bs4 import BeautifulSoup

from urllib2 import urlopen
from config import *

import urllib


def get_recent_scites (html, last_id): # {{{

    data  = defaultdict(list)
    soup  = BeautifulSoup(html, "html5lib")
    stuff = soup.find_all("li", class_="papers")


    if not stuff or len(stuff) <= 0:
        return True, data


    for thing in stuff:
        # We want the following. The arXiv ID
        arXiv_id = thing.find_all("a")[0].get("href").strip("/ ")

        if arXiv_id == last_id:
            return True, data

        # We'd also like the primary category.
        rcat     = thing.find_all("span", class_="identifier")[0].text
        category = general_category_for(re.findall("\[(.*)\]", rcat)[0])

        # And also the first author
        author = thing.find_all("div", 
                class_="authors")[0].find_all("a")[0].text

        surname = author.split(" ")[-1]
        clean_surname = urllib.quote(unicodedata.normalize('NFKD', surname).encode('ascii', 'ignore'))

        # Optimistic code lifetime assumption
        year    = str(datetime.datetime.now().year)[:2] + arXiv_id[:2]

        bibtex = "%s%s" % (clean_surname, year)

        data[category].append({"id": arXiv_id, "bibtex": bibtex})

        print arXiv_id, category, author, bibtex
    #
    return False, data
# }}}


groups = {
	"physics":   ["physics.", "hep-", "nucl-th", "gr-qc", "cond-mat."],
	"astro-ph":  ["astro-ph."],
	"quant":     ["quant-ph", "q-"],
	"math":      ["math.", "math-ph", "nlin"],
	"cs":        ["cs.", "stat."],
}

def general_category_for (category): # {{{
    for (g,v) in groups.iteritems():
        for prefix in v:
            if category.startswith(prefix):
                return g

    raise Exception("Can't categorise: %s" % (category,))
# }}}


def gen_scripts (data): # {{{
    """
        We have a dict of things like:

            { "quant-ph": [ {"id": "1302.5121", "bibtex": "Baez2013"}, ]}

        and we now want to use pybibtex to get the bibtex for this and also
        the PDF.
    """

    for (k, v) in data.iteritems():
        outf = open("%s.sh" % (k,), "w")
        outf.write("rm %s.bib\n\n" % (k,))
        for entry in v:
            outf.write('arxiv.py bib %s >> %s.bib\n' % (entry["id"], k))
            outf.write('wget --user-agent=Lynx http://arxiv.org/pdf/%(id)s -O "%(bibtex)s, %(id)s.pdf"\n' % entry)
            outf.write("\n\n")
        outf.close()
# }}}


def main (argv): # {{{

    last_id = argv[1]
    url     = "https://scirate3.herokuapp.com/users/" + str(USER_ID) + "/scites?page=%s"

    completed = False
    page = 1

    final = defaultdict(list)

    while not completed:
        print "Processing page %s" % (page,)

        html      = urlopen(url % (page,)).read()

        completed, data = get_recent_scites(html, last_id)


        for (k, v) in data.iteritems():
            final[k] += v

        page = page + 1
    #
    # Final contains the entire thing.
    #
    gen_scripts(final)
# }}}


if __name__ == "__main__":
    main(sys.argv)


def test_gen_scripts ():
    data = { "quant-ph": [ {"id": "1302.5121", "bibtex": "Baez2013"},
        {"id": "1305.5162", "bibtex": "Amcor2013"} ],
        "math": [ {"id": "1203.1922", "bibtex": "Madeup2013"}] }

    gen_scripts(data)


