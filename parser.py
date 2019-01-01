class ParseError(Exception):
  def __init__(self, rule=None, stream=None):
    self.rule = rule
    self.stream = stream

  def __str__(self):
    return ''.join(str(s) for s in self.stream) + '\nFiled rule: ' + str(self.rule)


class Rule:
  def __init__(self, val):
    self.val = val

  def __repr__(self):
    return '[' + ', '.join(str(v) for v in self.val) + ']'

  @classmethod
  def parse(cls, stream):
    for rule in cls.rules:
      try:
        if hasattr(rule, '__iter__'):
          parse = []
          new_stream = stream
          for r in rule:
            v, new_stream = r.parse(new_stream) 
            parse.append(v)
          return cls(parse), new_stream
        else:
          return rule.parse(stream)
      except ParseError:
        pass
    raise ParseError(rule=cls, stream=stream)


class Terminal(Rule):
  def __repr__(self):
    #return '%s(%s)' % (self.__class__, self.val)
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
      if token is not None:
        stream.append(token)
        token_found = True
        break
    if token is None:
      raise ValueError('Unrecognized:' + string)

  return stream
    
