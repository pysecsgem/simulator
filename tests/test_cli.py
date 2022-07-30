import pytest


class CLITestCase:
    def __init__(self, args):
        self.args = args
        self.exception = False


class CLITestCaseException:
    def __init__(self, args, exception_value, message):
        self.args = args
        self.exception = True
        self.exception_value = exception_value
        self.exception_message = message


cases = [
    CLITestCaseException([], "2", "error: the following arguments are required: command"),
    CLITestCaseException(["--help"], "0", "positional arguments:"),
]


@pytest.mark.parametrize("case", cases)
def test_cli(case, capsys):
    import secsgem_simulator.cli
    import secsgem_simulator.cli_tasks

    if case.exception:
        with pytest.raises(SystemExit) as exc:
            secsgem_simulator.cli.CommandLine(
                secsgem_simulator.cli_tasks.CLITask.commands()).parse(case.args)

        assert str(exc.value) == case.exception_value
        captured = capsys.readouterr()

        assert case.exception_message in captured.err or case.exception_message in captured.out
    else:
        pass


def test_cli_help():
    import secsgem_simulator.cli
    import secsgem_simulator.cli_tasks

    with pytest.raises(SystemExit) as exc:
        secsgem_simulator.cli.CommandLine(
            secsgem_simulator.cli_tasks.CLITask.commands()).parse(["help"])

    assert str(exc.value) == "2"
