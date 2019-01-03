import parser

# Some design notes:
#
#   The parse tree and the evaluation tree are one and the same. This makes
#   sense for trivial languages like this with no support for optimization,
#   compilation, or multiple backens. One day, I'll split these up.
#
#   I tried to make contexts (what scheme calls "environments", or what
#   hardware calls a stackframe) first order objects. I'm imagining you could
#   perform operations on them, like pass them around as objects, modify the
#   current context in a called subroutine, concatenate them, etc. I don't
#   know why you'd want to do this, but I wanted a way to experiment with this
#   ability.
#
#   I tried to make the parse tree a first order object too. The ~ operator
#   assigns the parse tree of the rhs to the lhs without evaluating the rhs.
#   Wherever the lhs is later evaluated, the parse tree is evaluated in
#   that context. I imagined this would be a nice way to decouple
#   functions from their environments. When you combine this with contexts as
#   first order objects, you get traditional closures for free. But hopefully
#   you can do more interesting things too. To be experimented with...
#

class Error:
  pass

class UnknownVariableError(Error):
  def __init__(self, context, varname):
    self.context = context
    self.varname = varname

  def __repr__(self):
    return 'Unknown variable %s.\nStacktrace:\n%s' % (
        self.varname,
        self.context.stacktrace())

class Context(object):
  """Evaluation contexts attach values to variables.

  If a name is not in the current context, it's looked up in the context's
  parent.
  """

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
      raise UnknownVariableError(self, name)

  def set_slot(self, name, value):
    self.slots[name] = value
    return value
 
  def stacktrace(self):
    return '   ' + str(self.context) + '\n' + (
        self.parent.stacktrace() if self.parent else '')

  def __str__(self):
    return 'Context{' + ', '.join(
        '%s:%s' % item for item in self.slots.iteritems()) + '}'


# ----- Objects in the parse tree.

class expr(parser.Rule):
  def eval(self, context):
    raise NotImplementedError

  def eval_lhs(self, context):
    return self.eval(context)

  def eval_rhs(self, context):
    return self.eval(context)

class expr_reference(expr):
  def __repr__(self):
    return "@" + str(self.val)

class expr_sequence(expr):
  def eval(self, context):
    # the value of a sequence is the value of its last element. all preceding
    # elements are evaluated for their side-effect only.
    self.val[0].eval(context)
    # the second term is either at index 2 if there's an intervening comma,
    # or at index 1 if there's no comma
    return self.val[-1].eval(context)

class expr_assignment(expr):
  def eval(self, context):
    lhs_varname = self.val[0].eval_lhs(context)
    rhs = self.val[2].eval_rhs(context)
    return context.set_slot(lhs_varname, rhs)

class expr_link(expr):
  def eval(self, context):
    # in the context of a link, the rhs isn't evaluated at all.
    lhs_varname = self.val[0].eval_lhs(context)
    rhs_ref = expr_reference(self.val[2])
    return context.set_slot(lhs_varname, rhs_ref)

class expr_plusminus(expr):
  def eval(self, context):
    op = {
      '+': int.__add__,
      '-': int.__sub__,
      '*': int.__mul__,
      '/': int.__div__
    }[self.val[1].val]

    # in non-assignment contexts, both operators are evaluated a rhs
    return op(self.val[0].eval_rhs(context),
              self.val[2].eval_rhs(context))

class expr_muldiv(expr_plusminus):
  pass

class context_definition(expr):
  def eval(self, context):
    assert isinstance(self.val[0], open_square_bracket)
    assert isinstance(self.val[-1], close_square_bracket)
    new_context = Context(parent=context)
    return self.val[1].eval(new_context)

class expr_highest_precedence(expr):
  def eval(self, context):
    if isinstance(self.val, integer):
      return self.val.eval(context)
    if isinstance(self.val[0], open_paren):
      # a parenthesized expression. return the expression inside
      return self.val[1].eval(context)
 

# ----- The terminal tokens

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
    while string and (string[0].isalnum() or string[0] == '_'):
      w += string[0]
      string = string[1:]

    return (cls(w) if w else None), string

  def eval_lhs(self, context):
    return self.val

  def eval_rhs(self, context):
    v = context.get_slot_rhs(self.val)
    if isinstance(v, expr_reference):
      return v.val.eval(context)
    return v

  def eval(self, context):
    return self.eval_rhs(context)


class op_assignment(parser.LiteralToken):
  tokens = {'='}

class op_link(parser.LiteralToken):
  tokens = {'~'}

class op_plusminus(parser.LiteralToken):
  tokens = {'-', '+'}

class op_muldiv(parser.LiteralToken):
  tokens = {'*', '/'}

class comma(parser.LiteralToken):
  tokens = {','}

class open_square_bracket(parser.LiteralToken):
  tokens = {'['}

class close_square_bracket(parser.LiteralToken):
  tokens = {']'}

class open_paren(parser.LiteralToken):
  tokens = {'('}

class close_paren(parser.LiteralToken):
  tokens = {')'}


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


# ----- The production rules.

expr_sequence.rules = (
    [expr, comma, expr_sequence],
    [expr, expr_sequence],
    expr,
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
