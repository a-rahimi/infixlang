#!/usr/bin/env python

import readline
import parser
import infixlang

def repl(stream=None):
  global_context = infixlang.Context()

  while True:
    try:
      ln = raw_input('>> ')
    except EOFError:
      break

    # tokenize the line
    try:
      tokens = infixlang.tokenize(ln)
    except parser.ParseError as e:
      print e
      continue

    # generate a parse tree for the line
    try:
      parse_tree, tokens = infixlang.expr_sequence.parse(tokens)
    except parser.ParseError as e:
      e.original_stream = tokens
      print e
      continue

    if tokens:
      print 'Warning: stuff unparsed on the line:', tokens

    # evaluate the line in the global context
    try:
      result = parse_tree.eval(global_context)
    except infixlang.Error as e:
      print e
      continue
    print result

if __name__ == '__main__':
  repl()
