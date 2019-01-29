# Infix arithmetic

This project started off as code golf for evaluating infix expressions like
this one:

  ```
  2 + 3 * 4 - 2 * (3-2)
  ```

(the answer is 12).

But it got out of hand.

# Features

* Obviously, the ability to parse and evaluate infix arithemtic expressions like the above.

* Support for variables, like so:
  ```
    a = 2 * 3
    b = a + 2
    b
  ```

  This evaluates to 8, as you'd expect.

* Support for closures and functions. Actually, there aren't any closures or functions. Instead, I decided to experiment with "contexts", a mix of a monad and an environment to propagate static single assignment expressions. They work like this:

    ```
      c ~ (b=a+2,  2*b)
      d = (a=2, c)
    ```

    The ~ notation assigns the parse tree of the rhs to the lhs. The rhs gets parsed, but not evaluated. Then wherever the lhs appears, the parse tree is evaluated in that context. Scoping is dynamic.

    In the above example, `c` is bound to the parse tree of the expression "b=a+2, 2*b". Evaluating that expression in the top level context would cause an error because the undefined `a` isn't defined there. The rhs in the next line defines the variable `a`, so `c` gets evaluated successfully in that context.

* You don't need delimeters between statements. The grammar is simple enough (or maybe the parser is smart enough) that you don't need to separate expressions with , or ;.  If you want to do so for clarity, you can. The above snippet can be written like this:

    ```
      c ~ (b= a + 2  2 * b),  d = (a=2  c)
    ```
    Though you probably wouldn't because it's much less readable.

* The special variable "this" returns the current context. When you evaluate a context-valued variable inside another context, the former updates the bindings in the latter. For example:

    ```
      >> con = (a=1, this)
      >> a
      Unknown variable a.
      >> (con a+1)
      2
    ```

* Error reporting. There's some.

* Conditional statements retrieve their condition, "then", and "else" clauses from the context. The `if` operator
  examines a variable named `cond`.  If it's nonzero, then the statement evaluates and returns a
  variable named `then`. If the condition is zero, a variable named `else` is evaluated and returned instead.
  If there is no `else` variable, `if` evaluates to 0. Here are some examples:

  This evaluates to 4:
  ```
    a=2, then=4 cond=(a==2) if
  ```

  A slightly more sophisticated example:

  ```
    r ~ (then=a*2 else=a*3 if)
    (a=1, cond=1, r)
  ```

  This evaluates to 2, and `(a=1, cond=0, r)` evaluates to 3.

  Recursion is easy now:

  ```
    factorial ~ (then~i*(i=i-1 factorial) else=1 cond=i if)
    (i=4 factorial)
  ```
  This returns 24.

# The Repl

There's an interactive environment. It works like this:

```
  arahimi$ ./repl.py
  >> a = 23
  >> b = 2
  >> c = a+b
  >> c
  25
  >> func ~ a+b
  @[a + b]
  >> (a=1, b=2, func)
  3
  >> func
  25
  >>
```

# About the language & implementation

## Grammar

Under the hood, there's a simple recursive descent context-free grammar parser.  What's nice
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

The value an assignment expression is a new context where the variable is endowed 
with a value:
```
 value(value(c: varname = e): varname) = value(c: e)
```

The value of a link expression is similar, except that the rhs is evaluated
twice in the new context:
```
 value(value(c: varname ~ unparsed_expr): varname) = value(c: value(c: unparsed_expr))
```

The "if" statements works like this:

```
 value(c: if e) = value(value(c: e): then)    if value(c: e) 
                  value(value(c: e): else)    else
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


# Language Maneuvers

The language doesn't have functions, closures, loops, or data structures, but
we can still build some typical language constructs with contexts and the "if" 
statement.


## Structs

You get structs for free when you pass around contexts like this:

  ```
   >> mystruct = (a=1, b=2, c=3, this)
   >> (mystruct b)
   2
  ```

The variable `mystruct` is just a context. The statement `(mystruct b)`
evaluates the variable `b` in that context.

## Iterators 

Iterators are structs endowed with a helper function that that returns an
updated sturct (keep in mind that we don't have functions or structs in this
language. I'm just using these terms to describe my own mental model of the 
next two lines):
```
iterate ~ (i=i+1, this)
iterator = (i=0 iterate)
```
Or better, we can encapsulate `iterate` inside `iterator` like so:
```
iterator = (i=0, iterate~(i=i+1, this), this)
```

You can query the state of an iterator as you would any other struct:
```
>> (iterator i)
1
>> (iterator i)
1
```

And you can advance through states:
```
>> iterator = (iterator iterate)
>> (iterator i)
2
```

## While Loops

A while loop advances an iterator to exhaustion. For the
purposes of a while loop, an iterator is exhausted when a variable
named `stop` evaluates to true in the iterator's context:

Here's how the while operator is defined:
```
while ~ (then=iterator, else~(iterator=(iterator iterate) while), cond=(iterator stop) if)
```

Here's an iterator that sums numbers from 1 to 8:
```
iterate ~ (i=i+1, sum=sum+i, stop=(i==8), this)
iterator = (i=0 sum=0 iterate)
```

Run the while loop to get the final iterator, then inspect the iterator:
```
>> iterator = while
>> (iterator i)
8
>> (iterator stop)
True
>> (iterator sum)
36
```

## Lists

We can build up linked lists by chaining contexts, and traversing that chain. Here's an example:
```
   insert ~ (prev=list, this)

   mylist = (this)
   mylist = (list=mylist value=2 insert)
   mylist = (list=mylist value=3 insert)
   mylist = (list=mylist value=7 insert)
```
`mylist` is a context with a variable named `value` and a varible named `prev`. 

Here's how to peel back the elements of the list:
```
>> (mylist value)
7
>> ((mylist prev) value)
3
>> (((mylist prev) prev) value)
2
```

## Associative Arrays

Here's a more sophisticated version of the above that implements associative
arrays:
```
  set_element ~ (prev=array, this)
  get_element ~ (then=(array value)
                 else~(array=(array prev) get_element)
                 cond=((array slot) == i)
                 if)

  myarray = (this)
  myarray = (array=myarray slot=1000 value=10 set_element)
  myarray = (array=myarray slot=2000 value=20 set_element)
  myarray = (array=myarray slot=3000 value=30 set_element)
```
The `get_element` function traverses the sequence of contexts embedded in the
array for one that has a matching `slot` variable, and returns its `value`
variable:

```
>> (array=myarray slot=1000 get_element)
10
>> (array=myarray slot=2000 get_element)
20
>> (array=myarray slot=3000 get_element)
30
```
