from collections import namedtuple

import attr


@attr.s(frozen=True, kw_only=True)
class Step:
    """Step wraps function stored as func parameter with the title
    and description for generating reports.
    """

    func = attr.ib(repr=False)
    description = attr.ib(
        factory=str, validator=attr.validators.instance_of(str)
    )
    title = attr.ib(factory=str, validator=attr.validators.instance_of(str))

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def _title_from_func_name(func_name):
    """Generates title for step from function name.
    Use only if given function name is in snake_case.
    """
    return " ".join(func_name.split("_")).capitalize() + "."


def _obj_doc(obj):
    """Retrieves documentation from given object. Returns empty
    string if there is no documentation at all.
    """
    return obj.__doc__ if obj.__doc__ is not None else ""


def step(f_or_title):
    """Decorator for generating Steps from custom functions."""

    def _factory(func):
        return Step(func=func, description=_obj_doc(func), title=f_or_title)

    try:
        return Step(
            func=f_or_title,
            title=_title_from_func_name(f_or_title.__name__),
            description=_obj_doc(f_or_title),
        )
    except AttributeError:
        # If we cannot retrieve function name, that means we have got
        # string, which represents title for step.
        return _factory


@attr.s(frozen=True, kw_only=True)
class State:
    """State holds data and another useful flag when running tests."""

    data = attr.ib(factory=dict, validator=attr.validators.instance_of(dict))
    break_execution = attr.ib(
        factory=bool, validator=attr.validators.instance_of(bool)
    )
    skipped = attr.ib(
        factory=bool, validator=attr.validators.instance_of(bool)
    )
    msg = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def is_failure(self):
        """Returns true if state was executed with failure."""
        return self.break_execution and not self.skipped

    def is_success(self):
        """Returns true if state was executed successfully."""
        return not self.break_execution and not self.skipped

    def is_skipped(self):
        """Returns true if state wasn't executed. This scenario
        mostly relates to steps that were skipped due to previous
        step being failed.
        """
        return self.skipped


def success(**kwargs):
    """Use when step has finished with success. You can use *args and **kwargs
    for sharing data between steps.
    """
    return State(
        data=kwargs,
        break_execution=False,
        skipped=False,
    )


def failure(msg):
    """Use when step has finished with failure. Pass custom failure message
    with msg attribute.
    """
    return State(msg=msg, break_execution=True, skipped=False)


def skip(step, reason=None):
    """Mark given step as skipped with given reason. Skip is pure function,
    which means, it returns copy of given state with factory for creating
    skipped state.
    """
    return attr.evolve(
        step,
        func=lambda: State(
            msg="Step skipped." if reason is None else reason,
            skipped=True,
        ),
    )


def _head_n_tail(seq):
    if len(seq) == 0:
        raise ValueError("Canno retrieve head and tail from empty sequence.")
    elif len(seq) == 1:
        return seq[0], []
    else:
        return seq[0], seq[1:]


Result = namedtuple("Result", ["step", "state"])


@attr.s(frozen=True, kw_only=True)
class Spec:
    """Spec represents data and methods for running single test suite
    scenario."""

    # TODO(thinkofher): Type error raised on validation is not readable.
    steps = attr.ib(validator=attr.validators.instance_of(tuple))
    description = attr.ib()
    title = attr.ib()

    def _run_step(self, step, **data):
        """Runs single step with given data and returns
        executed state.
        """
        try:
            state = step(**data)
        except Exception as e:
            # TODO(thinkofher): Include stack trace.
            state = failure(f"Exception {type(e)} occured.")

        return state

    def run_all(self, **init_data):
        """Runs all steps with given initial data and returns list
        of Results, which contains step and state of executed step.
        """
        result = list()
        init, rest = _head_n_tail(self.steps)

        state = self._run_step(init, **init_data)
        result.append(Result(step=init, state=state))

        for step in rest:
            if state.is_failure() or state.skipped:
                state = skip(step)()
            else:
                state = self._run_step(step, **state.data)
            result.append(Result(step=step, state=state))
        return result


def spec(title):
    """Decorator for generating test specifications with given title.
    Wrapps class with steps (tuple of Steps) field and transforms its doc
    string into specifications description.
    """

    def decorator(obj):
        desc = _obj_doc(obj)
        return Spec(steps=obj.steps, title=title, description=desc)

    return decorator
