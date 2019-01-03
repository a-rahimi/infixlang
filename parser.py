class ParseError(Exception):
  def __init__(self, message='', rule=None, stream=None):
    self.message = message
    self.rule = rule
    self.stream = stream
    self.original_stream = None

  def __str__(self):
    msg = self.message
    if self.original_stream:
      msg += '\nError at token %d:' % (
          len(self.original_stream) - len(self.stream))

    msg += '\n' + ''.join(str(s) for s in self.stream)
    if self.rule:
      msg += '\nFailed rule: ' + str(self.rule)
    return msg


class Rule(object):
  rules = None

  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return '[' + ' '.join(str(v) for v in self.val) + ']'

  @classmethod
  def parse(cls, stream):
    for rule in cls.rules:
      try:
        if hasattr(rule, '__iter__'):
          # try each production in order. report the result of the first one
          # that matches.
          parse = []
          new_stream = stream
          for r in rule:
            v, new_stream = r.parse(new_stream) 
            parse.append(v)
          return cls(parse), new_stream
        else:
          # the rule is an alias for another rule. just report its result.
          return rule.parse(stream)
      except ParseError:
        pass

    # none of the rules matched. fail.
    raise ParseError(message='No grammar rule matched', rule=cls, stream=stream)


class Terminal(Rule):
  def __repr__(self):
    return str(self.val)

  @classmethod
  def ismatch(cls, token):
    raise NotImplementedError

  @classmethod
  def tokenize(cls, string):
    if cls.ismatch(string[0]):
      return cls(string[0]), string[1:]
    return None, string

  @classmethod
  def parse(cls, stream):
    if not stream:
      raise ParseError(rule=cls, stream=stream)

    if not isinstance(stream[0], cls):
      raise ParseError(rule=cls, stream=stream)

    return stream[0], stream[1:]


def parse(production_rule_root, stream):
  """A convenience routine for parsing.

  This routine calls production_rule_root.parse(stream) and
  ensures that it's consumed the entire stream.
  """
  try:
    p, new_stream = production_rule_root.parse(stream)
  except ParseError as e:
    e.original_stream = stream
    raise e

  if new_stream:
    e = ParseError(
        message="Couldn't parse the entire stream",
        stream=new_stream)
    e.original_stream = stream
    e.parse_so_far = p
    raise e

  return p

# support for tokenizing the input

def eat_whitespace(string):
  while string and string[0].isspace():
    string = string[1:]
  return string

def tokenize(string, tokens):
  stream = []
  while string:
    string = eat_whitespace(string)
    for tok in tokens:
      token, string = tok.tokenize(string)
      if token:
        stream.append(token)
        break
    if not token:
      raise ParseError(message='Unrecognized:' + string,
                       stream=stream)

  return stream
