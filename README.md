# ExtendAnything

[![](https://img.shields.io/pypi/v/extendanything.svg)](https://pypi.python.org/pypi/extendanything)
[![CI](https://github.com/maximz/extendanything/actions/workflows/ci.yaml/badge.svg?branch=master)](https://github.com/maximz/extendanything/actions/workflows/ci.yaml)
[![](https://img.shields.io/badge/docs-here-blue.svg)](https://extendanything.maximz.com)
[![](https://img.shields.io/github/stars/maximz/extendanything?style=social)](https://github.com/maximz/extendanything)

ExtendAnything is a small Python helper for wrapping an already-created object
with a new interface. A wrapper class can add methods, override selected method
names, and still expose the original object's attributes without copying or
reinitializing the original instance.

The package is currently pre-alpha (`0.0.1`) and requires Python 3.8 or newer.

## Why it exists

Normal subclassing only helps before an object is created. ExtendAnything is for
cases where the instance already exists, such as a trained model, configured
client, or object returned by another library, and you want to attach
project-specific behavior around it.

Conceptually, it behaves like a lightweight dynamic cast: the wrapper handles
the behavior it defines, and missing attribute lookups fall through to the
wrapped object.

## How it works

Subclass `ExtendAnything`, accept the object to wrap, and call
`super().__init__(inner)`. The base class stores the original object on
`self._inner` and implements `__getattr__` so attributes and methods not found on
the wrapper are read from `self._inner`.

```python
from extendanything import ExtendAnything


class Predictor:
    def __init__(self, name):
        self.name = name

    def predict(self):
        return "base prediction"


class EnhancedPredictor(ExtendAnything):
    def __init__(self, inner, prefix):
        super().__init__(inner)
        self.prefix = prefix

    def predict(self):
        return f"{self.prefix}: {self._inner.predict()}"

    def explain(self):
        return f"{self.name} -> {self.predict()}"


base = Predictor("demo")
wrapped = EnhancedPredictor(base, "custom")

assert wrapped.name == "demo"  # forwarded to base
assert wrapped.predict() == "custom: base prediction"  # wrapper override
assert wrapped.explain() == "demo -> custom: base prediction"  # wrapper-only method
```

The wrapper also defines `__getstate__` and `__setstate__`, so wrapped objects can
round-trip through `pickle` and `joblib` when the wrapped object itself supports
that.

## Installation

The runtime package has no required third-party dependencies.

```bash
pip install extendanything
```

For local development from this repository:

```bash
pip install -r requirements_dev.txt
pip install -e .
```

## Important behavior

- Reads of missing attributes are forwarded to `self._inner`.
- Methods and attributes defined on the wrapper take precedence over the wrapped
  object.
- Assigning `wrapped.attr = value` writes to the wrapper, not to the inner
  object. To mutate the wrapped object, assign through `wrapped._inner.attr`.
- If the inner object changes, forwarded reads reflect those changes unless the
  wrapper has already set an attribute with the same name.
- Methods running inside the inner object still use the inner object's own
  method resolution. If an inner method calls `self.predict()`, it will not call
  a `predict()` override defined on the wrapper.
- The wrapper is not registered as a subclass of the wrapped object's class, so
  `isinstance(wrapped, InnerClass)` is false.
- Special methods such as indexing are not generally forwarded; use
  `wrapped._inner[...]` when direct access to the original object is needed.

## Development

```bash
make test
make lint
make docs
```

Tests cover attribute forwarding, wrapper overrides, attribute detachment,
`repr`, and `pickle`/`joblib` serialization.

ExtendAnything is released under the MIT license.
