# ExtendAnything (WIP)

[![](https://img.shields.io/pypi/v/extendanything.svg)](https://pypi.python.org/pypi/extendanything)
[![CI](https://github.com/maximz/extendanything/actions/workflows/ci.yaml/badge.svg?branch=master)](https://github.com/maximz/extendanything/actions/workflows/ci.yaml)
[![](https://img.shields.io/badge/docs-here-blue.svg)](https://extendanything.maximz.com)
[![](https://img.shields.io/github/stars/maximz/extendanything?style=social)](https://github.com/maximz/extendanything)


## Inject new functionality into Python objects

Extend any already-created Python object with new functionality, or replace its inner logic.

Suppose you trained a scikit-learn classifier and want to inject custom logic. The classifier instance already exists, and now you want it to have a `featurize()` method and a different rule for predicting class labels with `predict()`.

Here's how to modify the behavior of your existing scikit-learn classifier object with ExtendAnything:

```python
# pip install extendanything
from extendanything import ExtendAnything

# Create the original instance
clf = sklearn.linear_model.LogisticRegression().fit(X_train, y_train)

# Define a wrapper class with the functionality you want.
class CustomClassifier(ExtendAnything):
    # The constructor accepts the existing instance you want to wrap.
    def __init__(self, model):
        super().__init__(model)

    # Add functionality: introduce a brand new method.
    def featurize(self, df: pd.DataFrame) -> np.ndarray:
        X = df.values # ...
        return X

    # Replace the existing predict() with new logic:
    def predict(self, X: np.ndarray) -> np.ndarray:
        # For example, return the least likely class.
        # Here, classes_ and predict_proba come from the original model.
        return self.classes_[np.argmin(self.predict_proba(X), axis=-1)]

# Apply the wrapper
wrapped_clf = CustomClassifier(clf)

# Use standard scikit-learn classifier functionality
# These calls are passed through without modification
classes = wrapped_clf.classes_

# Use new or modified functionality
# These calls use your CustomClassifier's logic
X_test = wrapped_clf.featurize(df_test)
y_test = wrapped_clf.predict(X_test)
```

## What's happening here?

You can think of `CustomClassifier(clf)` as dynamically casting the scikit-learn classifier object to a subclass of your choice.

* Instantiate the `CustomClassifier` wrapper class by passing your existing object:`super().__init__(model)` sets `self._inner = model`.

* Get: Any unknown attribute accesses are passed through to `self._inner`. This means you can access the original object's attributes and methods, without defining them explicitly in the wrapper class.

* Set: Setting attributes detaches them, rather than modifying the inner instance.

* You can access the original object's functionality with `self._inner`.

* It's pickle-able.

## Limitations

* Logic defined in the base (wrapped) class can't access the derived (wrapper) class's overloaded methods.
  * Example: If you call `predict()` and that's not overloaded in your wrapper class, the call is passed through to your original wrapped instance. If `predict()` calls `predict_proba()`, it will use the original object's `predict_proba()`, _even if you created an overloaded `predict_proba()` in your wrapper class.

* Modifying attributes on the wrapped instance detaches those instance attributes, rather than modifying the inner instance.
  * Future accesses will hit the detached version belonging to the wrapper, not to the inner instance.
  * If needed, you can propogate changes to the inner instance by modifying `self._inner` directly. Attribute modifications directly on the base inner instance will be visible through the outer wrapped class's attributes, unless those attributes have already been detached by being modified on the outer instance.

* The final wrapped instance is not an official subclass of the original class. (It will not pass an `isinstance` check).

* Indexing like `[0]` is not currently passed through to the inner instance. For now use `.inner[0]`.

## Development

Submit PRs against `develop` branch, then make a release pull request to `master`.

```bash
# Install requirements
pip install --upgrade pip wheel
pip install -r requirements_dev.txt

# Install local package
pip install -e .

# Install pre-commit
pre-commit install

# Run tests
make test

# Run lint
make lint

# bump version before submitting a PR against master (all master commits are deployed)
bump2version patch # possible: major / minor / patch

# also ensure CHANGELOG.md updated
```

## TODOs: Configuring this template

Create a Netlify site for your repository, then turn off automatic builds in Netlify settings.

Add these CI secrets: `PYPI_API_TOKEN`, `NETLIFY_AUTH_TOKEN` (Netlify user settings - personal access tokens), `DEV_NETLIFY_SITE_ID`, `PROD_NETLIFY_SITE_ID` (API ID from Netlify site settings)

Set up Codecov at TODO
