#!/usr/bin/env python

import readline
import infixlang

def repl():
  global_context = infixlang.Context()
  tokens = []

  while True:
    try:
      ln = raw_input('>> ')
    except EOFError:
      break

    tokens = tokens + infixlang.tokenize(ln)
    parse_tree, tokens = infixlang.expr_sequence.parse(tokens)
    result = parse_tree.eval(global_context)
    print result


  
if __name__ == '__main__':
  repl()
