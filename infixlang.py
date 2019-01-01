import parser
reload(parser)


class integer(parser.Terminal):
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

  def eval(self):
    return self.val


class op1(parser.Terminal):
  """Infix operators with the lowest priority.

  These are + and -.
  """
  def __init__(self, val):
    self.val = val
    self.func = {'+': int.__add__, '-': int.__sub__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['-', '+']

class op2(parser.Terminal):
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

# Forward declarations of the production rules.
class expr(parser.Rule):
  pass

class expr1(parser.Rule):
  def eval(self):
    return self.val[1].func(self.val[0].eval(), self.val[2].eval())

class expr2(expr1):
  pass
 
class expr3(parser.Rule):
  def eval(self):
    if isinstance(self.val, integer):
      return self.val.eval()
    else:
      return self.val[1].eval()
  
 
# The actual production rules.
expr.rules = (expr1,)

expr1.rules = ([expr2, op1, expr1],
               expr2)

expr2.rules = ([expr3, op2, expr2],
               expr3)

expr3.rules = (integer,
               [open_paren, expr, close_paren])



def tokenize(string):
  return parser.tokenize(string, [integer, op1, op2, open_paren, close_paren])


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
  check('(2+3)*4')
  check('(2+3)*0')

  print 'OK'


def test_parsing():
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

  print 'OK'

def tests():
  test_tokenize()
  test_parsing()
