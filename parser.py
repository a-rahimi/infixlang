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
    return ' '.join(str(v) for v in self.val)

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
  def tokenize(cls, string):
    raise NotImplementedError

  @classmethod
  def parse(cls, stream):
    if not stream:
      raise ParseError(rule=cls, stream=stream)

    if not isinstance(stream[0], cls):
      raise ParseError(rule=cls, stream=stream)

    return stream[0], stream[1:]


class LiteralToken(Terminal):
  tokens = {}

  @classmethod
  def tokenize(cls, string):
    for token in cls.tokens:
      if string.startswith(token):
        return cls(token), string[len(token):]
    return None, string


# support for tokenizing the input

def eat_whitespace(string):
  while string and string[0].isspace():
    string = string[1:]
  return string

def tokenize(string, acceptable_tokens):
  parsed_tokens = []
  while string:
    string = eat_whitespace(string)
    if not string:
      break

    for tok in acceptable_tokens:
      token, string = tok.tokenize(string)
      if token:
        parsed_tokens.append(token)
        break

    if not token:
      raise ParseError(message='Unrecognized:' + string,
                       stream=parsed_tokens)

  return parsed_tokens
