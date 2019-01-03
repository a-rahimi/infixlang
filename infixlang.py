import parser
reload(parser)


class Context(object):

  class Slot(object):
    def __init__(self, context, name):
      self.context = context
      self.name = name

    def set_value(self, value):
      self.context.slots[self.name] = value

  def __init__(self, parent=None):
    self.slots = {}
    self.parent = parent

  def get_slot_rhs(self, name):
    if not isinstance(name, str):
      raise ValueError('"%s" is not a string' % name)

    try:
      return self.slots[name]
    except KeyError:
      if self.parent:
        return self.parent.get_slot_rhs(name)
      raise

  def get_slot_lhs(self, name):
    return self.Slot(self, name)

  def __str__(self):
    s = 'Context[' + ', '.join(str((s,v)) for s,v in self.slots.iteritems()) + ']'
    return s


global_context = Context()



class expr(parser.Rule):
  def eval(self, context):
    raise NotImplementedError

  def eval_lhs(self, context):
    return self.eval(context)

  def eval_rhs(self, context):
    return self.eval(context)

class expr_sequence(expr):
  def eval(self, context):
    assert len(self.val) in [1,2,3]

    r = self.val[0].eval(context)

    if len(self.val) == 3:
      assert isinstance(self.val[1], comma)
      assert isinstance(self.val[2], expr_sequence)
      return self.val[2].eval(context)
    elif len(self.val) == 2:
      assert isinstance(self.val[1], expr_sequence)
      return self.val[1].eval(context)

    return r

class expr_assignment(expr):
  def eval(self, context):
    # in the context of an assignment, the left operator is evaluated as lhs.
    return self.val[1].func(
        self.val[0].eval_lhs(context),
        self.val[2].eval_rhs(context))

class expr_link(expr):
  def eval(self, context):
    # in the context of a link, the left operator is evaluated as lhs,
    # and the rhs isn't evaluated at all.
    return self.val[1].func(
        self.val[0].eval_lhs(context),
        self.val[2])

class expr_plusminus(expr):
  def eval(self, context):
    # in non-assignment contexts, both operators are evaluated a rhs
    return self.val[1].func(
        self.val[0].eval_rhs(context),
        self.val[2].eval_rhs(context))

class expr_muldiv(expr_plusminus):
  pass

class context_definition(expr):
  def eval(self, context):
    assert isinstance(self.val[0], open_square_bracket)
    assert isinstance(self.val[1], expr_sequence)
    assert isinstance(self.val[-1], close_square_bracket)
    return self.val[1].eval(Context(parent=context))

class expr_highest_precedence(expr):

  def eval(self, context):
    if isinstance(self.val, integer):
      # an integer
      return self.val.eval(context)
    if isinstance(self.val[0], open_paren):
      # a parenthesized expression. return the expression and ignore the
      # parentheses.
      return self.val[1].eval(context)
 

class Value(parser.Terminal):
  def eval(self, context):
    return self.val

  def eval_lhs(self, context):
    return self.eval(context)

  def eval_rhs(self, context):
    return self.eval(context)


class integer(Value):
  @classmethod
  def tokenize(cls, string):
    ok = False
    num = 0
    while string:
      try:
        num = num * 10 + int(string[0])
      except ValueError:
        break
      string = string[1:]
      ok = True

    return (cls(num) if ok else None), string


class variable(Value):
  @classmethod
  def tokenize(cls, string):
    w = ''
    while string and string[0].isalnum():
      w += string[0]
      string = string[1:]

    return (cls(w) if w else None), string

  def eval_lhs(self, context):
    return context.get_slot_lhs(self.val)

  def eval_rhs(self, context):
    v = context.get_slot_rhs(self.val)
    if isinstance(v, Reference):
      return v.val.eval(context)
    return v

  def eval(self, context):
    return self.eval_rhs(context)


class op_assignment(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == '='

  def func(self, slot, rhs):
    slot.set_value(rhs)
    return rhs

class Reference(expr):
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return "@" + str(self.val)

class op_link(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == '~'

  def func(self, slot, rhs):
    rhs_ref = Reference(rhs)
    slot.set_value(rhs_ref)
    return rhs_ref

class op_plusminus(parser.Terminal):
  def __init__(self, val):
    self.val = val
    self.func = {'+': int.__add__, '-': int.__sub__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['-', '+']

class op_muldiv(parser.Terminal):
  def __init__(self, val):
    self.val = val
    self.func = {'*': int.__mul__, '/': int.__div__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['*', '/']

class comma(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == ','

class open_square_bracket(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == '['

class close_square_bracket(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == ']'

class open_paren(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == '('

class close_paren(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == ')'


# The actual production rules.
expr_sequence.rules = (
    [expr, comma, expr_sequence],
    [expr, expr_sequence],
    [expr],
    )

expr.rules = (
    expr_assignment,
    expr_link,
    expr_plusminus,
    )

expr_assignment.rules = (
    [variable, op_assignment, expr],
    )

expr_link.rules = (
    [variable, op_link, expr],
    )

expr_plusminus.rules = (
    [expr_muldiv, op_plusminus, expr_plusminus],
    expr_muldiv
    )

expr_muldiv.rules = (
    [expr_highest_precedence, op_muldiv, expr_muldiv],
    expr_highest_precedence)

context_definition.rules = (
    [open_square_bracket, expr_sequence, close_square_bracket], 
    )

expr_highest_precedence.rules = (
    integer,
    variable,
    [open_paren, expr, close_paren],
    context_definition,
    )


def tokenize(string):
  return parser.tokenize(string, [
    integer,
    op_assignment,
    op_link,
    op_plusminus,
    op_muldiv,
    open_paren,
    close_paren,
    open_square_bracket,
    close_square_bracket,
    comma,
    variable])


def test_tokenize():
  def check(string):
    tokens = tokenize(string)
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
    parse_tree = parser.parse(expr, tokenize(string))
    computed_value = parse_tree.eval(Context())
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
  context = Context()
  parser.parse(expr, tokenize('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46
  parser.parse(expr, tokenize('bar = foo + 2')).eval(context)
  assert context.slots['bar'] == 48

  context = Context()
  tokens = tokenize('a = 2* 23   b = a + 2 b')
  p, tokens = expr.parse(tokens)
  p.eval(context)
  p, tokens = expr.parse(tokens)
  p.eval(context)
  p, tokens = expr.parse(tokens)
  assert p.eval(context) == 48
  assert not tokens
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48
  print 'OK assignment'


def test_expr_sequence():
  context = Context()
  parser.parse(expr_sequence, tokenize('foo = 2 * 23')).eval(context)
  assert context.slots['foo'] == 46

  tokens = tokenize('a = 2* 23,  b = a + 2')
  p = parser.parse(expr_sequence, tokens)
  context = Context()
  assert p.eval(context) == 48
  assert context.slots['a'] == 46
  assert context.slots['b'] == 48

  tokens = tokenize('a = 2* 23,  b = a + 2, b')
  p = parser.parse(expr_sequence, tokens)
  context = Context()
  assert p.eval(context) == context.slots['b']

  print 'OK expr sequence'



def test_contexts():
  context = Context()
  tokens = tokenize('a = 2* 3, c = [b = a + 2, 2*b]')
  p = parser.parse(expr_sequence, tokens)
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16

  context = Context()
  tokens = tokenize('a = 2* 3 c = [b = a + 2, 2*b]')
  p = parser.parse(expr_sequence, tokens)
  assert p.eval(context) == 16
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['c'] == 16


  context = Context()
  tokens = tokenize('a = 2* 3, d = [aa=2, [b = aa + 2, 2*b]]')
  p = parser.parse(expr_sequence, tokens)
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8

  context = Context()
  tokens = tokenize('a = 2* 3  d = [aa=2  [b = aa + 2    2*b]]')
  p = parser.parse(expr_sequence, tokens)
  assert p.eval(context) == 8
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert context.slots['d'] == 8


  context = Context()
  tokens = tokenize('a = [2], b = [a]')
  p = parser.parse(expr_sequence, tokens)
  p.eval(context)
  assert context.slots['b'] == 2

  context = Context()
  tokens = tokenize('a ~ [3], b = [a]')
  p = parser.parse(expr_sequence, tokens)
  assert p.eval(context) == 3
  assert context.slots['b'] == 3

  context = Context()
  tokens = tokenize('a = 2* 3, c ~ [b = aa + 2, 2*b], d = [aa=2, c]')
  p = parser.parse(expr_sequence, tokens)
  p.eval(context)
  assert context.slots['a'] == 6
  assert 'b' not in context.slots
  assert 'c' in context.slots
  assert context.slots['d'] == 8

  context = Context()
  tokens = tokenize('a = 2* 3    c ~ [b = aa + 2     2*b]    d = [aa=2 c]')
  assert parser.parse(expr_sequence, tokens).eval(context) == 8
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
