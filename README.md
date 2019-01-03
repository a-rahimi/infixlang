# Oops, this turned into a programming language

You shouldn't use any of the code from this. You'll also probably not learn
anything good from it.

When I was in high school, I tried to write code to parse and evaluate infix
expressions with operator precendence, like this:

  ```
  2 + 3 * 4 - 2 * (3-2)
  ```

(the answer is 12).

It's is one of those problems every child should solve at some point, but I
never cracked it as a kid. My solutions never could handle all expressions in their
generality correctly (depending on my attempt, parentheses would be hard to handle,
or it'd get tripped up by operator precedence, or whatever).

Now I'm an adult, on a week-long vacation, with some time on my hands (or rather,
desperately in need for some time to myself). So I'm tackling this problem again.

Except I ended up writing the college version of this.

## Features

* A full parser that can handle context-free grammars defined as python
    expressions. The production rules for this language are written in python. They look
    like this:

  ```python
  expr.rules = (
      expr_assignment,
      expr_link,
      expr_plusminus,
      )

  expr_plusminus.rules = (
      [expr_muldiv, op_plusminus, expr_plusminus],
      expr_muldiv
      )

  expr_muldiv.rules = (
      [expr_highest_precedence, op_muldiv, expr_muldiv],
      expr_highest_precedence
      )
  ```

* Obviously, the ability to parse and evaluate infix arithemtic expressions like the above.

* Support for variables, like so:
  ```
  a = 2 * 3,  b = a + 2
  ```

  This evaluates to 8, as you'd expect.

* Support for closures and functions. Um. This project got out of hand, and I
    wanted to experiment with this:

    ```
      c ~ [b = a + 2     2*b]
      d = [a=2 c]
    ```

    The ~ notation assigns the parse tree of the rhs to the lhs. The rhs gets parsed, but not evaluated. Then wherever the lhs appears, the parse tree is evaluated in that context. The `[...]` notation creates a new evaluation environment where variables are bound. These can nest. Scoping is dynamic.

    In the above example, `c` is bound to an expression that creates a new context. That expression can't be evaluated in the top level context because it refers to the variable `a`, which is unbound. The next line creates a new context which does define a variable `a`. It can therefore evaluate the context that was bound to `c`. The context `[a=2 c]` is evaluated (its result is 8), and assigne to the variable `d`.

* You don't need delimeters between statements. The grammar is simple enough (or maybe the parser is smart enough?) that you don't need to separate expressions with , or ;. But if you need to do so for clarity, you can. The snippet can be written like this:

    ```
      c ~ [b = a + 2, 2*b],  d = [a=2, c]
    ```

* Error reporting. There's some. On my next vacation, maybe I'll leverage Python's exception system to generate nicer error reports.

# The Repl

There's an interactive environment. It works like this:

```
  arahimi$ ./repl.py
  >> a= 23
  23
  >> b = 2
  2
  >> c = a+b
  25
  >> func ~ a+b
  @[a + b]
  >> [a=1, b=2, func]
  3
  >> func
  25
  >>
```

Here's what happened in that session. There's nothing surprising in the first
three lines. The line `func ~ a+b` defines a variable `func` that points to the
parse tree of the expression `a+b`. The next line creates a context in which
a=1, b=2, and evaluates `func` in that context. The final line evaluates
`func` in the global context where a=23, b=2.
