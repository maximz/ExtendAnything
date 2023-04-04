# Wrap a class instance

import joblib
import pytest
import pickle

from extendanything import ExtendAnything


class SimpleClassifier:
    fixed_name = "static"

    def __init__(self, dynamic_name):
        self.dynamic_name = dynamic_name

    @property
    def classes_(self):
        return ["classA", "classB"]

    def extra_method(self):
        return "Simple Extra Method" + self.predict()

    def predict(self):
        return "Simple Predict"

    def use_predict(self):
        return self.predict()


class AdjustedClassifier(ExtendAnything):
    def __init__(self, inner, extra_arg):
        # sets self._inner
        super().__init__(inner)
        self.extra_arg = extra_arg

    def predict(self):
        return "Overloaded Predict" + self._inner.predict()

    def new_method(self):
        # Also call a method only defined in base class - which will in turn call the base class's predict(), not the overloaded version!
        return "Brand new" + self.extra_arg + self.extra_method()


def test_extend_anything():
    base_classifier = SimpleClassifier("dynamic")
    assert base_classifier.fixed_name == "static"
    assert base_classifier.dynamic_name == "dynamic"
    assert base_classifier.predict() == "Simple Predict"
    assert base_classifier.extra_method() == "Simple Extra Method" + "Simple Predict"

    # modify before wrapping to make sure init isn't called again somehow
    base_classifier.fixed_name = "static2"
    base_classifier.dynamic_name = "dynamic2"

    # wrap this instance of SimpleClassifier
    wrapped_classifier = AdjustedClassifier(base_classifier, "extra arg")
    # overloading base class
    assert wrapped_classifier.predict() == "Overloaded Predict" + "Simple Predict"
    # accessing base class's elements not defined explicitly on wrapper class
    assert wrapped_classifier.extra_method() == "Simple Extra Method" + "Simple Predict"
    assert wrapped_classifier.fixed_name == "static2"
    assert wrapped_classifier.dynamic_name == "dynamic2"
    # brand new method on derived class only
    assert (
        wrapped_classifier.new_method()
        == "Brand new" + "extra arg" + "Simple Extra Method" + "Simple Predict"
    )

    # what happens if we modify base_classifier.dynamic_name? will it affect wrapped_classifier? it should!
    base_classifier.dynamic_name = "dynamic3"
    assert base_classifier.dynamic_name == wrapped_classifier.dynamic_name == "dynamic3"

    # what happens if we modify wrapped_classifier.fixed_name? will it affect base_classifier? it shouldn't!
    # this acts like a copy - it detaches the attribute from the inner object.
    wrapped_classifier.fixed_name = "static_wrapped"
    assert base_classifier.fixed_name == "static2"
    assert wrapped_classifier.fixed_name == "static_wrapped"

    # to propogate changes to base_classifier, we must modify _inner directly
    wrapped_classifier._inner.fixed_name = "static_wrapped_propogate_change"
    assert base_classifier.fixed_name == "static_wrapped_propogate_change"
    # but notice that fixed_name on the wrapped instance is unchanged, because we detached it by modifying it above. so be thoughtful about when to modify _inner.
    # TODO: is there some setattr overriding we want to do to make this cleaner?
    assert wrapped_classifier.fixed_name == "static_wrapped"

    # Note that logic defined in the base class can't access the derived class's overloaded methods! This is a big limitation
    assert wrapped_classifier.use_predict() == "Simple Predict"

    # the AdjustedClassifier instance is not auto-registered as a subclass of SimpleClassifier
    assert isinstance(base_classifier, SimpleClassifier)
    assert isinstance(wrapped_classifier, AdjustedClassifier)
    assert not isinstance(wrapped_classifier, SimpleClassifier)


def test_extend_anything_repr():
    base_classifier = SimpleClassifier("dynamic")
    # wrap this instance of SimpleClassifier
    wrapped_classifier = AdjustedClassifier(base_classifier, "extra arg")
    assert repr(wrapped_classifier) == "AdjustedClassifier: " + repr(base_classifier)


def test_extend_anything_pickleable(tmp_path):
    """
    Test that class instance wrapper objects can be pickled.
    This requires us to override __getstate__ and __setstate__. See notes in the main class.
    """
    base_classifier = SimpleClassifier("dynamic")
    # wrap this instance of SimpleClassifier
    wrapped_classifier = AdjustedClassifier(base_classifier, "extra arg")
    assert wrapped_classifier.predict() == "Overloaded Predict" + "Simple Predict"

    # make sure pickleable and unpickaleable
    wrapped_classifier_loaded = pickle.loads(pickle.dumps(wrapped_classifier))
    assert (
        wrapped_classifier_loaded.predict() == "Overloaded Predict" + "Simple Predict"
    )

    # repeat with joblib
    # get temp file using https://docs.pytest.org/en/latest/how-to/tmp_path.html
    fname = tmp_path / "wrapper.joblib"
    joblib.dump(wrapped_classifier, fname)
    wrapped_classifier_loaded = joblib.load(fname)
    assert (
        wrapped_classifier_loaded.predict() == "Overloaded Predict" + "Simple Predict"
    )


class WrongUsage(ExtendAnything):
    def __init__(self):
        # This is an example of wrong usage -- do not do this.
        # We just want to test what happens if this child class tries to access a non-existent self attribute before calling super init.
        # See comment in the main class where we declare `_inner = None``.
        print(self.something_that_doesnt_exist)


@pytest.mark.xfail(raises=AttributeError)
def test_wrong_usage_does_not_cause_infinite_recursion():
    # We want this to trigger AttributeError: 'NoneType' object has no attribute 'something_that_doesnt_exist'
    # Instead of RecursionError: maximum recursion depth exceeded while calling a Python object
    WrongUsage()
