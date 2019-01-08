# Infix arithmetic

This project started off as code golf for evaluating infix expressions like
this one:

  ```
  2 + 3 * 4 - 2 * (3-2)
  ```

(the answer is 12).

But it got out of hand and became a programming language.


# Features

* Obviously, the ability to parse and evaluate infix arithemtic expressions like the above.

* Support for variables, like so:
  ```
    a = 2 * 3
    b = a + 2
  ```

  This evaluates to 8, as you'd expect.

* Support for closures and functions. Actually, there aren't any closures or functions. Instead, I decided to experiment with "contexts", a mix of a monad and an environment. They work like this:

    ```
      c ~ (b = a + 2,  2*b)
      d = (a=2 c)
    ```

    The ~ notation assigns the parse tree of the rhs to the lhs. The rhs gets parsed, but not evaluated. Then wherever the lhs appears, the parse tree is evaluated in that context. Scoping is dynamic.

    In the above example, `c` is bound to the parse tree of the expression "b=a+2, 2*b". Evaluating that expression in the top level context would cause an error because the undefined `a` isn't defined there. The rhs in the next line defines the variable `a`, so `c` gets evaluated successfully in that context.

* You don't need delimeters between statements. The grammar is simple enough (or maybe the parser is smart enough) that you don't need to separate expressions with , or ;.  If you want to do so for clarity, you can. The above snippet can be written like this:

    ```
      c ~ (b=a+2  2*b),  d = (a=2  c)
    ```

* The special variable "this" returns the current context. When you evaluate a context-valued variable inside another context, the former updates the bindings in the latter. For example:

    ```
      >> con = (a=1, this)
      ...
      >>> a
      Unknown variable a.
      >> (con a+1)
      2
    ```

  You get structs for free when you pass around contexts like this:
  ```
   >> mystruct = (a=1, b=2, c=3, this)
   ...
   >> (mystruct b)
   2
  ```

* Error reporting. There's some.

* Conditional statements retrieve their "then" and "else" clauses from the context. The `if <condition>` operator
  evaluates condition.  If it's nonzero, then the statement evaluates and returns a variable 
  named `then`. If the condition is zero, a
  variable named `else` is evaluated and returned instead. If there is no `else`
  variable, `if` evaluates to `cond`. Here are some examples:

  This evaluates to 4:
  ```
    a=2, then=4 if a==2
  ```

  A slightly more sophisticated example:

  ```
    r ~ (then=a*2 else=a*3 if cond)
    (a=1, cond=1, r)
  ```

  This evaluates to 2, and `(a=1, cond=0, r)` evaluates to 3.

  Recursion is easy now:

  ```
    factorial ~ (then~i*(i=i-1 factorial) else=1 if i)
    (i=4 factorial)
  ```
  This returns 24.

  Here's a function that accumulates i<sup>2</sup> up to some i. It returns 30
  for i=4:

  ```
    accumulate ~ (tally=tally+func, then~(i=i-1 accumulate), else~tally, if i)
    (tally=0 i=4 func~i*i accumulate)
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
  >> (a=1, b=2, func)
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


# About the language & implementation

## Grammar

Under the hood, there's a very simple simple recursive descent context-free grammar parser.  What's nice
about this particular parser is that it only takes 110 lines of code, and the production rules can
themselves be written in Python. Here is a snippet from the code:

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


## Formal Language Semantics

There are no side effects in the language. Instead, values are propagated
thrugh contexts. Contexts form a hierarchy for looking up variables. 

A context has two attributes: a parent and a value.  parent(c) is just the parent of c.
value(c: expr) is the value of an expression in a context c. For example, 
value(c: a + b) is the value of a+b in the the context of c, and value(parent(c): a + b)
is its value in the parent context of c.

Every expression evaluates to a context. A chain of contexts is generated for
a sequence of expressions:
```
 value(c: e1, e2, ...) = value(value(c: e1): e2, ...)
```
A consequence of this rule is that the value of a sequence of expressions is
the value of the last element.

If a variable name isn't in a context, it's looked up in the context's parent:
```
 value(c: varname) = value(parent(c): varname) if varname ∉ c
```

Contexts distribute over arithmetic operations (op can be -+/*=):
```
 value(c: e1 op e2) = value(c: value(c: e1) op value(c: e2))
```

The link operator is treated slightly differently from other binary operators:
```
 value(c: e1 ~ e2) = value(c: value(c: e1) ~ e2)
```

The value of the = and ~ opeators is a new context where the variable is endowed with
a value:
```
 value(value(c: varname = e): varname) = value(c: e)
 value(value(c: varname ~ e): varname) = value(c: e)
```

The "if" statements works like this:

```
 value(c: if e) = value(value(c if e): then) if value(c: e) 
                                             else value(value(c: if e): else)
```

There is a special variable named "this". It returns the context where "this" is being evaluated:
```
 value(c: this) = c
```

Evaluating a context inside another context causes subsequent expressions to
inherit from the context.
```
 value(c: context, e1, ...) = value(chain(c, context): e1, ...)
```
where chain(c1, c2) returns a new context where c1 is the parent of the root
of c2. This hopefully explains the "mystruct" example above.
