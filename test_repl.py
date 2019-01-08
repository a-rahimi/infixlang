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

def test_counting():
  in_string = """
    counter_state = 0
    cnt = 0
    count ~ (counter_state, cnt=cnt+1, this)
    counter_state = count
    (counter_state cnt)
    counter_state = count
    counter_state = count
    (counter_state cnt)
    (counter_state cnt)
    counter_state = count
    (counter_state cnt)
    """
  istream = StringIO.StringIO(in_string)
  ostream = StringIO.StringIO()
  estream = StringIO.StringIO()

  repl.repl(istream, ostream, estream)

  assert estream.getvalue() == ''

  olines = ostream.getvalue().split('\n')
  assert olines[7] == '1'
  assert olines[73] == '3'
  assert olines[74] == '3'
  assert olines[232] == '4'

  #for i, ln in enumerate(olines): print i, ':', ln
