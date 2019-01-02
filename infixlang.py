import collections

import parser
reload(parser)


# Forward declarations of the production rules.
class expr(parser.Rule):
  def eval(self):
    raise NotImplementedError

  def eval_lhs(self):
    return self.eval()

  def eval_rhs(self):
    return self.eval()

class expr_assignment_like(expr):
  def eval(self):
    return self.val[1].func(self.val[0].eval_lhs(), self.val[2].eval_rhs())

class expr2(expr):
  def eval(self):
    return self.val[1].func(self.val[0].eval_rhs(), self.val[2].eval_rhs())

class expr3(expr2):
  pass
 
class expr4(expr3):
  def eval(self):
    if isinstance(self.val, integer):
      # an integer
      return self.val.eval()
    if isinstance(self.val[0], open_paren):
      # a parenthesized expression. return the expression and ignore the
      # parentheses.
      return self.val[1].eval()
 

class Value(parser.Terminal):
  def eval(self):
    return self.val

  def eval_lhs(self):
    return self.eval()

  def eval_rhs(self):
    return self.eval()


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

    return cls(num) if ok else None, string

class Context(object):
  def __init__(self):
    self.slots = {}

  def get_slot_rhs(self, name):
    if not isinstance(name, str):
      raise ValueError('"%s" is not a string' % name)

    return self.slots[name]

  def get_slot_lhs(self, name):
    return Slot(self, name)

class Slot(object):
  def __init__(self, context, name):
    self.context = context
    self.name = name

  def set_value(self, value):
    self.context.slots[self.name] = value


# for now, there just a global context. eventually, i'll chain these into
# frames.
context = Context()


class word(Value):
  """A standin for a top level expression.

  A word can be assigned to an expression like this:
     myword = 1 + 23 * 43

  From there, wherever "myword" appears, a reference to the expression
  object corresponding to 1 + 23 * 43 is substituted. 
  """
  @classmethod
  def tokenize(cls, string):
    w = ''
    while string and not string[0].isspace():
      w += string[0]
      string = string[1:]

    return cls(w), string

  def eval_lhs(self):
    return context.get_slot_lhs(self.val)

  def eval_rhs(self):
    return context.get_slot_rhs(self.val)


class op_assignment(parser.Terminal):
  """Infix operators with the lowest priority.

  This is just =.
  """
  def __init__(self, val):
    self.val = val

  @classmethod
  def ismatch(cls, token):
    return token == '='

  def func(self, lhs, rhs):
    lhs.set_value(rhs)
    return rhs


class op_plusminus(parser.Terminal):
  """Infix operators with the lowest priority.

  These are + and -.
  """
  def __init__(self, val):
    self.val = val
    self.func = {'+': int.__add__, '-': int.__sub__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['-', '+']

class op_muldiv(parser.Terminal):
  """Infix operators with the second lowest priority.

  These are * and /.
  """
  def __init__(self, val):
    self.val = val
    self.func = {'*': int.__mul__, '/': int.__div__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['*', '/']

class open_paren(parser.Terminal):
  """A single character literal: (.
  """
  @classmethod
  def ismatch(cls, token):
    return token == '('

class close_paren(parser.Terminal):
  """A single character literal: ).
  """
  @classmethod
  def ismatch(cls, token):
    return token == ')'


# The actual production rules.
expr.rules = (expr_assignment_like,)

expr_assignment_like.rules = ([word, op_assignment, expr2],
               expr2)

expr2.rules = ([expr3, op_plusminus, expr2],
               expr3)

expr3.rules = ([expr4, op_muldiv, expr3],
               expr4)

expr4.rules = (integer,
               word,
               [open_paren, expr, close_paren])


def tokenize(string):
  return parser.tokenize(string, [
    integer,
    op_assignment,
    op_plusminus,
    op_muldiv,
    open_paren,
    close_paren,
    word])


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
    computed_value = parse_tree.eval()
    if computed_value != expected_value:
      raise ValueError('Got %s expected %s for %s' % (
        computed_value,
        expected_value, 
        string))
    print string, '=', expected_value

  check('2+3*4', 14)
  check('2 *  3 +4', 10)
  check('(2+3)*4', 20)
  check('(2+3)*0', 0)

  print 'OK parse'

def test_assignment():
    parser.parse(expr, tokenize('foo = 2 * 23')).eval()
    assert context.slots['foo'] == 46
    parser.parse(expr, tokenize('bar = foo + 2')).eval()
    assert context.slots['bar'] == 48

    tokens = tokenize('a = 2* 23   b = a + 2')
    p, tokens = expr.parse(tokens)
    p.eval()
    p, tokens = expr.parse(tokens)
    p.eval()
    assert not tokens
    assert context.slots['a'] == 46
    assert context.slots['b'] == 48
    print 'OK'


def tests():
  test_tokenize()
  test_parse()
  test_assignment()
