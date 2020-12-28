# encoding: utf-8

'''Utilities'''

import rdflib


def readRDF(uri):
    '''Parse the RDF at `uri` and return the statements made in the form of `{s→{p→[o]}}` where
    `s` is a subject URI, `p` is a predicate URI, and `[o]` is a sequence of objects which may
    be literals or URIs.
    '''
    graph = rdflib.Graph()
    graph.parse(uri)
    statements = {}
    for s, p, o in graph:
        if s not in statements:
            statements[s] = {}
        predicates = statements[s]
        if p not in predicates:
            predicates[p] = []
        predicates[p].append(o)
    return statements
