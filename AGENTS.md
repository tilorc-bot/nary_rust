# Style

Write no prose. Show what the code does with an example that a test runs.

## Docstrings

Only doctests. One line of text above a group of examples is allowed.

Good:

```python
def domain_of(e):
    """
    >>> domain_of(log(y + 1))
    Ne(Add(y, 1), 0)
    """
```

Bad:

```python
def domain_of(e):
    """Return the domain of the application ``e``: the domain of its head
    with each parameter replaced by the argument in its position.
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

- After removing prose, run `python tests/test_prose.py` and commit the
  lower budget.
- Do not raise a number or add a file to the budget unless the owner asks.
