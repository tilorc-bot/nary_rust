# Style

Write no prose. Show what the code does with an example that a test runs.

## Docstrings

Doctests. One line of text above a group of examples is allowed.

Where the name and the parameters do not say what a function does, the
first line may be one simple sentence that does.

Good:

```python
def domain_of(e):
    """
    >>> domain_of(log(y + 1))
    Ne(Add(y, 1), 0)
    """


def _has_a_value(e, known):
    """Whether e is known to have a value, given the conditions that known says hold.

    >>> _has_a_value(log(x), lambda condition: condition == Ne(x, 0))
    True
    """
```

Bad:

```python
def domain_of(e):
    """Return the domain of the application ``e``: the domain of its head
    with each parameter replaced by the argument in its position.
    """
```

## Parameters and result

A public function may also say what each parameter is and what the function
returns, in Google style, between the first line and the examples.

- `Args:` has one entry for each parameter, in the order of the signature.
- `Returns:` has one entry.
- No types: the signature has them.
- No other section and no other paragraph.
- Use what a reader can type and check, such as `e.head` or `known(condition)`,
  not a term that needs a definition.
- Leave out what an example shows and what reading the code answers.

Good:

```python
def rewrite(e, rules, known=None):
    """Apply the rules to e until none applies.

    Args:
        e: The expression to rewrite.
        rules: The rules to try, in order.
        known: Called as known(condition). A rule with a condition applies
            only where this returns True.

    Returns:
        The rewritten expression.

    >>> rewrite(x / x, rules, known=lambda condition: True)
    1
    """
```

Bad:

```python
def rewrite(e, rules, known=None):
    """Apply the rules to e until none applies.

    The engine walks the expression bottom-up and restarts after each
    rule that applies.

    Args:
        e (Expr): The expression to rewrite.
    """
```

## Comments

None, in Python, Rust, Lean, TOML and YAML.

| The comment would say | Do this instead |
|---|---|
| what the code does | rename or restructure the code |
| how the code behaves | add a doctest or a test |
| a decision that is still open | open an issue |

## Markdown

No README and no other Markdown file.

## The check

`tests/test_prose.py` counts the lines of prose in each file and compares
them with `tests/prose_budget.txt`. A file that is not listed has a budget
of 0.

- The first line of a docstring is not counted, and neither are `Args:` and
  `Returns:` on a public function when `Args:` has the parameters in order.
- After removing prose, run `python tests/test_prose.py` and commit the
  lower budget.
- Do not raise a number or add a file to the budget unless the owner asks.
