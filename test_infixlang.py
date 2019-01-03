import parser
import infixlang

def test_tokenize():
  def check(string):
    tokens = infixlang.tokenize(string)
    stringified = ''.join(str(tok) for tok in tokens)
    expected = string.translate(None, ' ')
    if stringified != expected:
      raise ValueError('Got %s for %s' % (
        stringified,
        expected))

  check('2+3*4')
  check('2 *  3 +4')
  check('(2 +3)*4')
  check('( 2+3 )*0')
  check('foo = 23 * 2  bar = foo * 2')

  print 'OK tokenize'


def test_parse():
  def check(string, expected_value):
    parse_tree = parser.parse(infixlang.expr, infixlang.tokenize(string))
    computed_value = parse_tree.eval(infixlang.Context())
    if computed_value != expected_value:
      raise ValueError('Got %s expected %s for %s' % (
        computed_value,
        expected_value, 
        string))

  check('2+3*4', 14)
  check('2 *  3 +4', 10)
  check('(2+3)*4', 20)
  check('(2+3)*0', 0)

  print 'OK parse'


def test_assignment():
  context = infixlang.Context()
  parser.parse(infixlang.expr, infixlang.tokenize('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46

  parser.parse(infixlang.expr, infixlang.tokenize('bar = foo + 2')).eval(context)
  assert context.slots['bar'] == 48

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 23   b = a + 2 b')
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  assert p.eval(context) == 48
  assert not tokens
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48
  print 'OK assignment'


def test_expr_sequence():
  context = infixlang.Context()
  parser.parse(infixlang.expr_sequence, infixlang.tokenize('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46

  tokens = infixlang.tokenize('a = 2* 23,  b = a + 2')
  p = parser.parse(infixlang.expr_sequence, tokens)
  context = infixlang.Context()
  assert p.eval(context) == 48
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48

  tokens = infixlang.tokenize('a = 2* 23,  b = a + 2, b')
  p = parser.parse(infixlang.expr_sequence, tokens)
  context = infixlang.Context()
  assert p.eval(context) == context.slots['b']

  print 'OK expr sequence'


def test_contexts():
  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 3, c = [b = a + 2, 2*b]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 3 c = [b = a + 2, 2*b]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 3, d = [aa=2, [b = aa + 2, 2*b]]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 3  d = [aa=2  [b = aa + 2    2*b]]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = [2], b = [a]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  p.eval(context)
  assert context.slots['b'] == 2

  context = infixlang.Context()
  tokens = infixlang.tokenize('a ~ [3], b = [a]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  assert p.eval(context) == 3
  assert context.slots['b'] == 3

  context = infixlang.Context()
  tokens = infixlang.tokenize('a = 2* 3, c ~ [b = aa + 2, 2*b], d = [aa=2, c]')
  p = parser.parse(infixlang.expr_sequence, tokens)
  p.eval(context)
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert 'c' in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  tokens = infixlang.tokenize("""
      a = 2 * 3
      c ~ [b = aa + 2     2*b]
      d = [aa=2 c]""")
  assert parser.parse(infixlang.expr_sequence, tokens).eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert 'c' in context.slots
  assert context.slots['d'] == 8

  print 'OK contexts'


def tests():
  test_tokenize()
  test_parse()
  test_assignment()
  test_expr_sequence()
  test_contexts()
