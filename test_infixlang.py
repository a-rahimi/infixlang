"""Run these tests with nose:

  nosetests -v
"""
import parser
import infixlang

# aliases for commonly used operations
T = infixlang.tokenize
P = parser.parse

def test_tokenize():
  def check(string):
    stringified = ''.join(str(tok) for tok in T(string))
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
    parse_tree = P(infixlang.expr, T(string))
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
  P(infixlang.expr, T('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46
  P(infixlang.expr, T('bar = foo + 2')).eval(context)
  assert context.slots['foo'] == 46
  assert context.slots['bar'] == 48

  context = infixlang.Context()
  tokens = T('a = 2* 23   b = a + 2 b')
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  assert not tokens
  assert p.eval(context) == 48
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48

  context = infixlang.Context()
  tokens = T('a_bbbb = 2*23   b_a = a_bbbb + 2 a_bbbb')
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  assert not tokens
  assert p.eval(context) == 46
  assert context.slots['a_bbbb'] == 46
  assert context.slots['b_a'] == 48

  print 'OK assignment'


def test_expr_sequence():
  context = infixlang.Context()
  P(infixlang.expr_sequence, T('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46

  context = infixlang.Context()
  p = P(infixlang.expr_sequence, T('a = 2* 23,  b = a + 2'))
  assert p.eval(context) == 48
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48

  context = infixlang.Context()
  p = P(infixlang.expr_sequence, T('a = 2* 23,  b = a + 2, b'))
  assert p.eval(context) == context.slots['b']

  print 'OK expr sequence'


def test_contexts():
  context = infixlang.Context()
  p = P(infixlang.expr_sequence, T('a = 2* 3, c = [b = a + 2, 2*b]'))
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16

  context = infixlang.Context()
  p = P(infixlang.expr_sequence, T('a = 2* 3 c = [b = a + 2, 2*b]'))
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16

  context = infixlang.Context()
  p = P(infixlang.expr_sequence,
        T('a = 2* 3, d = [aa=2, [b = aa + 2, 2*b]]'))
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  p = P(infixlang.expr_sequence,
       T('a = 2* 3  d = [aa=2  [b = aa + 2 2*b]]'))
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  p = P(infixlang.expr_sequence, T('a = [2], b = [a]'))
  assert p.eval(context) == 2
  assert context.slots['b'] == 2

  context = infixlang.Context()
  p = parser.parse(infixlang.expr_sequence, T('a ~ [3], b = [a]'))
  assert p.eval(context) == 3
  assert context.slots['b'] == 3

  context = infixlang.Context()
  p = P(infixlang.expr_sequence, 
        T('a = 2* 3, c ~ [b = aa + 2, 2*b], d = [aa=2, c]'))
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert 'c' in context.slots
  assert context.slots['d'] == 8

  context = infixlang.Context()
  tokens = T("""
      a = 2 * 3
      c ~ [b = aa + 2     2*b]
      d = [aa=2 c]""")
  assert P(infixlang.expr_sequence, tokens).eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert 'c' in context.slots
  assert context.slots['d'] == 8

  print 'OK contexts'
