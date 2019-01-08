"""Run these tests with nose:

  nosetests -v
"""
import parser
import infixlang

# commonly used operations throughout the tests
T = infixlang.tokenize
C = infixlang.Context

def parse(production_rule_root, stream):
  """Parse & ensure token stream is fully consumed.
  """
  try:
    p, stream_rest = production_rule_root.parse(stream)
  except parser.ParseError as e:
    e.original_stream = stream
    raise e

  if stream_rest:
    e = parser.ParseError(
        message="Couldn't parse the entire stream",
        stream=stream_rest)
    e.original_stream = stream
    e.parse_so_far = p
    raise e

  return p


def test_tokenize():
  def check(string):
    stringified = ''.join(str(tok) for tok in T(string))
    expected = string.translate(None, ' ')
    if stringified != expected:
      raise ValueError('Got %s for %s' % (
        stringified,
        expected))

  check('2+3 == 5')
  check('2+3*4')
  check('2 *  3 +4')
  check('(2 +3)*4')
  check('( 2+3 )*0')
  check('foo = 23 * 2  bar = foo * 2')

  print 'OK tokenize'


def test_parse():
  def check(string, expected_value):
    parse_tree = parse(infixlang.expr, T(string))
    computed_value = parse_tree.eval(C()).val
    if computed_value != expected_value:
      raise ValueError('Got %s expected %s for %s' % (
        computed_value,
        expected_value, 
        string))

  check('2+3*4', 14)
  check('2 *  3 +4', 10)
  check('(2+3)*4', 20)
  check('(2+3)*0', 0)
  check('(2+3) == 5', 1)
  check('(2+3) == 4', 0)

  print 'OK parse'


def test_assignment_1():
  context = C()
  parse(infixlang.expr, T('foo = 2 * 23')).eval(context)
  assert context['foo'] == 46
  parse(infixlang.expr, T('bar = foo + 2')).eval(context)
  assert context['foo'] == 46
  assert context['bar'] == 48

def test_assignment_2():
  context = C()
  tokens = T('a = 2* 23   b = a + 2 b')
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  assert not tokens
  v = p.eval(context).val
  assert v == 48
  assert context['a'] == 46
  assert context['b'] == 48

def test_assignment_3():
  context = C()
  tokens = T('a_bbbb = 2*23   b_a = a_bbbb + 2 a_bbbb')
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  p.eval(context)
  p, tokens = infixlang.expr.parse(tokens)
  assert not tokens
  v = p.eval(context).val
  assert v == 46
  assert context['a_bbbb'] == 46
  assert context['b_a'] == 48


def test_expr_sequence_1():
  context = parse(infixlang.expr_sequence, T('foo = 2 * 23')).eval(C())
  assert context['foo'] == 46

def test_expr_sequence_2():
  context = parse(infixlang.expr_sequence,
            T('a = 2* 23,  b = a + 2')).eval(C())
  assert context.val == 48
  assert context['a'] == 46
  assert context['b'] == 48

def test_expr_sequence_3():
  context = parse(infixlang.expr_sequence,
            T('a = 2* 23,  b = a + 2, b')).eval(C())
  assert context.val == context['b']


def test_contexts_1():
  context = parse(infixlang.expr_sequence, 
            T('a = 2* 3, c = (b = a + 2, 2*b)')).eval(C())
  assert context.val == 16
  assert context['a'] == 6
  assert 'b' not in context
  assert context['c'] == 16

def test_contexts_2():
  context = parse(infixlang.expr_sequence,
            T('a = 2* 3 c = (b = a + 2, 2*b)')).eval(C())
  assert context.val == 16
  assert context['a'] == 6
  assert 'b' not in context
  assert context['c'] == 16

def test_contexts_3():
  context = parse(infixlang.expr_sequence,
            T('a = 2* 3, d = (aa=2, (b = aa + 2, 2*b))')).eval(C())
  assert context.val == 8
  assert context['a'] == 6
  assert 'b' not in context
  assert context['d'] == 8

def test_contexts_4():
  context = parse(infixlang.expr_sequence,
            T('a = 2* 3  d = (aa=2  (b = aa + 2 2*b))')).eval(C())
  assert context.val == 8
  assert context['a'] == 6
  assert 'b' not in context
  assert context['d'] == 8

def test_contexts_5():
  context = parse(infixlang.expr_sequence,
            T('a = (2), b = (a)')).eval(C())
  assert context.val == 2
  assert context['b'] == 2

def test_contexts_6():
  context = parse(infixlang.expr_sequence,
            T('a ~ (3), b = (a)')).eval(C())
  assert context.val == 3
  assert context['b'] == 3

def test_contexts_7():
  context = parse(infixlang.expr_sequence, 
            T('a = 2* 3, c ~ (b = aa + 2, 2*b), d = (aa=2, c)')
           ).eval(C())
  assert context.val == 8
  assert context['a'] == 6
  assert 'b' not in context
  assert 'c' in context
  assert context['d'] == 8

def test_contexts_8():
  tokens = T("""
      a = 2 * 3
      c ~ (b = aa + 2     2*b)
      d = (aa=2 c)""")
  context = parse(infixlang.expr_sequence, tokens).eval(C())
  assert context.val == 8
  assert context['a'] == 6
  assert 'b' not in context
  assert 'c' in context
  assert context['d'] == 8


def test_if_1():
  tokens = T("""
      else = 4
      then = 2
      if 0
      """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 4

def test_if_2():
  tokens = T("""
      else ~ 2 * a
      then ~ 3 * a
      a = 2
      if 0
      """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 4

def test_if_3():
  tokens = T("""
      a = 1
      else ~ 2 * a
      then ~ 3 * a
      a = 2
      if 1
      """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 6

def test_if_4():
  tokens = T("""
      a = 1
      else ~ (b = 2, b * a)
      then ~ (b = 3, b * a)
      a = 2
      if 1
      """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 6

def test_if_5():
  tokens = T("""
      a = 2
      else ~ 2*a  then ~ 3*a  if  a == 2
      """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 6

def test_if_6():
  tokens = T("""
    r ~ (then ~ a*2, else ~ a*3, if cond)
    l0 = (a=1, cond=0, r)
    l1 = (a=1, cond=1, r)
    """)
  context = parse(infixlang.expr_sequence, tokens).eval(C())
  assert context.val == 2
  assert context['l0'] == 3
  assert context['l1'] == 2


def test_variable_context_1():
  tokens = T("""
    con = (a=1, b=2, this)
    (c=3, con, a+c)
    """)
  context = parse(infixlang.expr_sequence, tokens).eval(C())
  assert context.val == 4

def test_variable_context_2():
  tokens = T("""
    con = (a=1, (b=2, this))
    (c=3, con, a+b+c)
    """)
  context = parse(infixlang.expr_sequence, tokens).eval(C())
  assert context.val == 6


def test_factorial():
  tokens = T("""
    factorial ~ (then ~ i*(i=i-1 factorial) else=1 if i)
    (i=4 factorial)
    """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 24


def test_accumulate():
  tokens = T("""
    accumulate ~ (tally=tally+func, then~(i=i-1 accumulate), else~tally, if i)
    (tally=0 i=4 func~i*i accumulate)
    """)
  v = parse(infixlang.expr_sequence, tokens).eval(C()).val
  assert v == 30
