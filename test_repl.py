import StringIO
import repl

def interaction(in_string, expected_output_string, expected_error_string):
  istream = StringIO.StringIO(in_string)
  ostream = StringIO.StringIO()
  estream = StringIO.StringIO()

  repl.repl(istream, ostream, estream)

  assert ostream.getvalue() == expected_output_string
  assert estream.getvalue() == expected_error_string

def test_variables():
  in_string = """
    a = 23
    b = a * 2
  """
  interaction(in_string, '23\n46\n', '')

def test_error():
  in_string = """
    4 ^ 7
  """
  interaction(in_string, '', 'Unrecognized:^ 7\n\n4\n')

def test_overflow_warning():
  in_string = """
    a = 2 *
  """
  interaction(in_string, '2\n', 'Warning: stuff unparsed on the line: [*]\n')
