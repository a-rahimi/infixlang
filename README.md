# Infix arithmetic

You shouldn't use any of the code from this. You'll also probably not learn
anything good from it.

When I was in high school, I tried to write code to parse and evaluate infix
expressions with operator precedence, like this:

  ```
  2 + 3 * 4 - 2 * (3-2)
  ```

(the answer is 12).

It's one of those problems most programming fans solve early on in their
lives, but my solutions as a youth never could handle all expressions in their
generality correctly (depending on my attempt, parentheses would be hard to handle,
or I'd get tripped up by operator precedence, or I'd face some infinite
recursion). I knew about the [Shunting-Yard](https://en.wikipedia.org/wiki/Shunting-yard_algorithm)
algorithm, but like Pierre Menard, I wanted to invent it myself.


# Oops, this turned into a programming language

Now I'm an adult, on a family vacation, with some time on my hands (or rather,
desperately in need for some time to myself). So I'm tackling this problem once 
again after 25 years.

It kind of got out of hand.


## Features

* A context-free grammar parser (basically, YACC + Lex in 110 lines of Python). What's nice about this
  particular parser is that the production can themselves be written in Python. Here is a snippet from 
  the code:

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
    a = 2 * 3
    b = a + 2
  ```

  This evaluates to 8, as you'd expect.

* Support for closures and functions. This is where the project got out of hand. I was
  having so much fun writing this that I ended up implementing more features,
  like this:

    ```
      c ~ [b = a + 2     2*b]
      d = [a=2 c]
    ```

    The ~ notation assigns the parse tree of the rhs to the lhs. The rhs gets parsed, but not evaluated. Then wherever the lhs appears, the parse tree is evaluated in that context. The `[...]` notation creates a new evaluation environment where variables are bound. These can nest. Scoping is dynamic.

    In the above example, `c` is bound to an expression that creates a new context. If we tried to evaluate that expression in the top level context, we'd get an error because it refers to the undefined variable `a`. The rhs in the next line creates a new context which does define a variable `a`. It can therefore evaluate the context that was bound to `c`. The context `[a=2 c]` is evaluated (its result is 8), and assigne to the variable `d`.

* You don't need delimeters between statements. The grammar is simple enough (or maybe the parser is smart enough) that you don't need to separate expressions with , or ;. But if you need to do so for clarity, you can. The above snippet can be written like this:

    ```
      c ~ [b = a + 2, 2*b],  d = [a=2, c]
    ```

* Error reporting. There's some. On my next vacation, maybe I'll leverage Python's exception system to generate nicer error reports.

* Conditional statements use the context heavily to avoid cluttering the grammar
  and the semantics of the language. The `if <condition>` operator evaluates the condition.
  If it's nonzero, then the statement evaluates and returns a variable in
  the context named `then`. If the condition is zero, instead
  variable in the context named `else` is evaluated and return. If there is no `else`
  variable in the context, `if` evaluates to `cond`. Here are some examples:

  ```
  >> a = 2
  2
  >> then = 4
  4
  >> if a==2
  4
  >>
  ```

  A slightly more sophicicated one:

  ```
  >> r ~ [then ~ a*2, else ~ a*3, if cond]
  @[[ [[then ~ [a * 2]] , [[else ~ [a * 3]] , [if cond]]] ]]
  >> [a=1, cond=1, r]
  2
  >> [a=1, cond=0, r]
  3
  >>
  ```

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

Here's what's happening in this session: Nothing surprising in the first
three lines. The line `func ~ a+b` defines a variable `func` that points to the
parse tree of the expression `a+b`. The next line creates a context in which
a=1, b=2, and evaluates `func` in that context. The final line evaluates
`func` in the global context where a=23, b=2.
