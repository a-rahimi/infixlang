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
      if not ln:
        raise EOFError
    except EOFError:
      break

    if ln.isspace():
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
      result = parse_tree.eval(global_context)
    except infixlang.Error as e:
      print >>estream, e
      continue

    print >>ostream, result

if __name__ == '__main__':
  repl()
