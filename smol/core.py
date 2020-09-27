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


def _step_doc(func):
    """Retrieves documentation from given function. Returns empty
    string if there is no documentation at all.
    """
    return func.__doc__ if func.__doc__ is not None else ""


def step(f_or_title):
    """Decorator for generating Steps from custom functions."""

    def _factory(func):
        return Step(func=func, description=_step_doc(func), title=f_or_title)

    try:
        return Step(
            func=f_or_title,
            title=_title_from_func_name(f_or_title.__name__),
            description=_step_doc(f_or_title),
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
        return self.break_execution and not self.skipped


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


def run_steps(steps, init_data=None):
    result = []
    init, rest = _head_n_tail(steps)

    try:
        if init_data is not None:
            state = init(**init_data)
        else:
            state = init()
    except Exception as e:
        state = failure(f"Exception {type(e)} occured.")
        result.append(Result(step=init, state=state))

    for step in rest:
        if state.is_failure() or state.skipped:
            state = skip(step)()
        else:
            try:
                state = step(**state.data)
            except Exception as e:
                state = failure(f"Exception {type(e)} occured.")

        result.append(Result(step=step, state=state))

    return result
