import attr

from smol.core import failure, run_steps, step, success
from smol.toolz import unpack


@step
def add_two_numbers(**kwargs):
    """Returns succesfully sum of two given numbers."""
    a, b = unpack(kwargs, "a", "b")
    return success(result=a + b)


def add(num):
    @step(f"Add {num}.")
    def _add_step(**kwargs):
        result = unpack(kwargs, "result")
        return success(result=result + num)

    desc = f"Adds {num} to given result."
    return attr.evolve(_add_step, description=desc)


def substract(num):
    @step(f"Substract {num}.")
    def _sub_step(**kwargs):
        result = unpack(kwargs, "result")
        return success(result=result - num)

    desc = f"Substract {num} from given result."
    return attr.evolve(_sub_step, description=desc)


def result_is(num):
    @step(f"Given result is {num}.")
    def _result_step(**kwargs):
        result = unpack(kwargs, "result")
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

    res = run_steps(steps, init_data={"a": 10, "b": 40})
    pprint.pprint(res)
    print(all(not result.state.skipped for result in res))
