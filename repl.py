#!/usr/bin/env python

import sys
import readline

import parser
import infixlang

def repl(istream=None, ostream=sys.stdout, estream=sys.stderr):
  global_context = infixlang.Context()

  while True:
    try:
      ln = istream.readline() if istream else raw_input('>> ')
      if istream and not ln:
        raise EOFError
    except EOFError:
      break

    if not ln or ln.isspace():
      # ignore blank lines. they're not in the language grammar
      continue 

    # tokenize the line
    try:
      tokens = infixlang.tokenize(ln)
    except parser.ParseError as e:
      print >>estream, e
      continue

    # generate a parse tree for the line
    try:
      parse_tree, tokens = infixlang.expr_sequence.parse(tokens)
    except parser.ParseError as e:
      e.original_stream = tokens
      print >>estream, e
      continue

    if tokens:
      print >>estream, 'Warning: stuff unparsed on the line:', tokens

    # evaluate the line in the global context
    try:
      global_context = parse_tree.eval(global_context)
    except infixlang.Error as e:
      print >>estream, e
      continue

    # collapse the global context to avoid chaining one context per command line
    global_context = infixlang.Context(val=global_context.val,
                                       slots=global_context.dictify())

    if global_context.val is not None:
      print >>ostream, global_context.val

if __name__ == '__main__':
  import pdb, traceback, sys

  try:
    repl()
  except:
    extype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)

