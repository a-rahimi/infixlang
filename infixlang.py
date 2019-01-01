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
  def __init__(self, val):
    self.val = val
    self.func = {'+': int.__add__, '-': int.__sub__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['-', '+']

class op2(parser.Terminal):
  def __init__(self, val):
    self.val = val
    self.func = {'*': int.__mul__, '/': int.__div__}[val] 

  @classmethod
  def ismatch(cls, token):
    return token in ['*', '/']

class open_paren(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == '('

class close_paren(parser.Terminal):
  @classmethod
  def ismatch(cls, token):
    return token == ')'

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
  
 
expr.rules = (expr1,)

expr1.rules = ([expr2, op1, expr1],
               expr2)

expr2.rules = ([expr3, op2, expr2],
               expr3)

expr3.rules = (integer,
               [open_paren, expr, close_paren])



def tokenize(string):
  return parser.tokenize(string, [integer, op1, op2, open_paren, close_paren])

def tests():
  def check(string, expected_value):
    parse_tree, remaining_stream = expr.parse(tokenize(string))
    computed_value = parse_tree.eval()
    if computed_value != expected_value:
      raise ValueError('Got %s expected %s for %s' % (
        computed_value,
        expected_value, 
        string))
    return remaining_stream

  check('2+3*4', 14)
  check('2 *  3 +4', 10)
  check('(2+3)*4', 20)

  print 'OK'
