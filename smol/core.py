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
class Data:
    """Represents data that can be shared (but not mutated) from one
    step to another.
    """

    args = attr.ib(factory=tuple)
    kwargs = attr.ib(factory=dict)


@attr.s(frozen=True, kw_only=True)
class State:
    """State holds data and another useful flag when running tests."""

    data = attr.ib(
        factory=lambda: Data(), validator=attr.validators.instance_of(Data)
    )
    break_execution = attr.ib(
        factory=bool, validator=attr.validators.instance_of(bool)
    )
    skipped = attr.ib(factory=bool, validator=attr.validators.instance_of(bool))
    msg = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def is_failure(self):
        return self.break_execution == True and self.skipped == False


def success(*args, **kwargs):
    """Use when step has finished with success. You can use *args and **kwargs
    for sharing data between steps.
    """
    return State(
        data=Data(args=args, kwargs=kwargs),
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

    if init_data is not None:
        state = init(*init_data.args, **init_data.kwargs)
    else:
        state = init()
    result.append(Result(step=init, state=state))

    for step in rest:
        if state.is_failure() or state.skipped:
            state = skip(step)()
        else:
            state = step(*state.data.args, **state.data.kwargs)
        result.append(Result(step=step, state=state))

    return result


@step
def add_two_numbers(a, b, *args, **kwargs):
    """Returns succesfully sum of two given numbers."""
    return success(result=a + b)


def add(num):
    @step(f"Add {num}.")
    def _add_step(result):
        return success(result=result + num)

    desc = f"Adds {num} to given result."
    return attr.evolve(_add_step, description=desc)


def substract(num):
    @step(f"Substract {num}.")
    def _sub_step(result):
        return success(result=result - num)

    desc = f"Substract {num} from given result."
    return attr.evolve(_sub_step, description=desc)


def result_is(num):
    @step(f"Given result is {num}.")
    def _result_step(result):
        if result == num:
            return success(result=result)
        else:
            return failure(f"Given result {result} is not equal to {num}.")

    desc = f"Checks whether given result is equal to {num}."

    return attr.evolve(_result_step, description=desc)


if __name__ == "__main__":
    steps = [
        add_two_numbers,
        result_is(50),
        add(10),
        add(5),
        substract(15),
        add(1),
        result_is(51),
    ]
    import pprint

    res = run_steps(steps, init_data=Data(args=(20, 30)))
    pprint.pprint(res)
    print(all(not result.state.skipped for result in res))
