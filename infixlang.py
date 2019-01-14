import parser

# Some design notes:
#
#   The parse tree and the evaluation tree are one and the same. This makes
#   sense for trivial languages like this with no support for optimization,
#   compilation, or multiple backens. One day, I'll split these up.
#
#   I tried to make contexts (what scheme calls "environments", or what
#   hardware calls a stackframe) first order objects.
#
#   I tried to make the parse tree a first order object too. The ~ operator
#   assigns the parse tree of the rhs to the lhs without evaluating the rhs.
#   Wherever the lhs is later evaluated, the parse tree is evaluated in
#   that context. When you combine this with contexts as first order objects,
#   you get traditional closures for free, among other things.

class Error:
  pass

class UnknownVariableError(Error):
  def __init__(self, context, varname):
    self.context = context
    self.varname = varname

  def __repr__(self):
    return 'Unknown variable %s.\nStacktrace:\n%s' % (
        self.varname, self.context.stacktrace())

class Context(object):
  def __init__(self, parent=None, val=None, slots={}):
    self.parent = parent
    self.val = val
    self.slots = slots

  def dictify(self):
    slots = self.parent.dictify() if self.parent else {}
    slots.update(self.slots)
    return slots

  def __getitem__(self, name):
    if name == 'this':
      return self

    try:
      return self.slots[name]
    except KeyError:
      if self.parent:
        return self.parent[name]
      raise UnknownVariableError(self, name)

  def __contains__(self, name):
    return name in self.slots or (
        name in self.parent if self.parent else False)

  def stacktrace(self, current_depth=0, max_depth=-1):
    return '%d: ' % current_depth + str(self) + (
        '\n' + self.parent.stacktrace(current_depth+1, max_depth-1)
        if self.parent or not max_depth else '')

  def __str__(self):
    return 'Context(%s){%s}' %( 
        self.val,
        ', '.join('%s:%s' % item for item in self.slots.iteritems()))


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
    c0 = self.val[0].eval(context)
    return self.val[-1].eval(
        Context(parent=c0, val=c0.val, slots=c0.val.dictify())
        if isinstance(c0.val, Context) else c0)

class expr_assignment(expr):
  def eval(self, context):
    varname = self.val[0].eval_lhs(context).val
    rhs = self.val[2].eval_rhs(context)
    return Context(parent=context, 
                   val=varname if isinstance(rhs.val, Context) else rhs.val,
                   slots={varname: rhs.val})

class expr_link(expr):
  def eval(self, context):
    # in the context of a link, the rhs isn't evaluated at all.
    varname = self.val[0].eval_lhs(context).val
    rhs_val = expr_reference(self.val[2])
    return Context(parent=context, val=rhs_val, slots={varname: rhs_val})

class expr_equality(expr):
  def eval(self, context):
    op = {
      '+': int.__add__,
      '-': int.__sub__,
      '*': int.__mul__,
      '/': int.__div__,
      '==': lambda x,y: not int.__cmp__(x,y),
    }[self.val[1].val]

    lhs = self.val[0].eval(context).val
    rhs = self.val[2].eval(context).val
    return Context(parent=context, val=op(lhs, rhs))

class expr_plusminus(expr_equality):
  pass

class expr_muldiv(expr_equality):
  pass

class parenthesized_expr(expr):
  def eval(self, context):
    return Context(parent=context, val=self.val[1].eval(context).val)

class expr_highest_precedence(expr):
  pass



# ----- The terminal tokens.

class Value(parser.Terminal):
  def eval(self, context):
    return Context(parent=context, val=self.val)

  def eval_lhs(self, context):
    return self.eval(context)

  def eval_rhs(self, context):
    return self.eval(context)


class integer(Value):
  @classmethod
  def tokenize(cls, string):
    ok = False
    num = 0
    while string and string[0].isdigit():
      num = num * 10 + int(string[0])
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
    return Context(parent=context, val=self.val)

  def eval_rhs(self, context):
    v = context[self.val]
    if isinstance(v, expr_reference):
      return v.val.eval(context)
    return Context(parent=context, val=v)

  def eval(self, context):
    return self.eval_rhs(context)


class op_assignment(parser.LiteralToken):
  tokens = {'='}

class op_link(parser.LiteralToken):
  tokens = {'~'}

class op_plusminus(parser.LiteralToken):
  tokens = {'-', '+'}

class op_equality(parser.LiteralToken):
  tokens = {'=='}

class op_muldiv(parser.LiteralToken):
  tokens = {'*', '/'}

class comma(parser.LiteralToken):
  tokens = {','}

class open_paren(parser.LiteralToken):
  tokens = {'('}

class close_paren(parser.LiteralToken):
  tokens = {')'}

class op_if(parser.LiteralToken):
  tokens = {'if'}

  def eval(self, context):
    truth_context = variable('cond').eval(context)
    if truth_context.val:
      return variable('then').eval(truth_context)
    else:
      try:
        return variable('else').eval(truth_context)
      except UnknownVariableError:
        return truth_context


def tokenize(string):
  return parser.tokenize(string, [
    integer,
    op_equality,
    op_plusminus,
    op_muldiv,
    op_assignment,
    op_link,
    op_if,
    open_paren,
    close_paren,
    comma,
    variable])


# ----- The production rules.

expr_sequence.rules = (
    [expr, comma, expr_sequence],
    [expr, expr_sequence],
    expr,
    )

expr.rules = (
    op_if,
    expr_assignment,
    expr_link,
    expr_equality,
    )

expr_assignment.rules = (
    [variable, op_assignment, expr],
    )

expr_link.rules = (
    [variable, op_link, expr],
    )

expr_equality.rules = (
    [expr_plusminus, op_equality, expr_equality],
    expr_plusminus
    )

expr_plusminus.rules = (
    [expr_muldiv, op_plusminus, expr_plusminus],
    expr_muldiv
    )

expr_muldiv.rules = (
    [expr_highest_precedence, op_muldiv, expr_muldiv],
    expr_highest_precedence
    )

parenthesized_expr.rules = (
    [open_paren, expr_sequence, close_paren],
    )

expr_highest_precedence.rules = (
    parenthesized_expr,
    integer,
    variable,
    )
