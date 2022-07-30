"""Command line parser."""
import argparse
import sys
import typing

from secsgem_simulator.cli_tasks import CLITask


class CommandLine:  # pylint: disable=too-few-public-methods
    """Defines the available command line arguments."""

    def __init__(self, commands: typing.List[typing.Type[CLITask]],):
        """Initialize the parser structure.

        Args:
            commands: list of command tasks to use

        """
        self.parser = argparse.ArgumentParser()

        self.subparsers = self.parser.add_subparsers(help='commands', dest="command", required=True)

        for command in commands:
            sub_parser = self.subparsers.add_parser(command.name(), help=command.help())
            self._add_command_arguments(command, sub_parser)

    @staticmethod
    def _add_command_arguments(command: typing.Type[CLITask], sub_parser: argparse.ArgumentParser):
        """Add the arguments of a command to a parser.

        Args:
            command: cli task type
            sub_parser: target argument parser

        """
        for arg in command.args():
            kwargs = arg.copy()
            del kwargs["name"]

            sub_parser.add_argument(arg["name"], **kwargs)

    def parse(self, args: typing.List[str]) -> argparse.Namespace:
        """Run the parser on the command line structure.

        Args:
            args: command line arguments

        Returns:
            Parsed arguments

        """
        return self.parser.parse_args(args)


def main():
    """Entry point for the command line interface."""
    arguments = CommandLine(CLITask.commands()).parse(sys.argv[1:])

    task = CLITask.from_args(arguments)
    task.run()
