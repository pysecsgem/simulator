"""Command line tasks."""
import argparse
import multiprocessing.connection
import os
import pathlib
import sys
import typing

import secsgem_simulator.command_server
import secsgem_simulator.script_runner

SERVER_ARGS: typing.List[typing.Dict[str, typing.Any]] = [
    {
        "name": "--host",
        "default": "localhost",
        "dest": "server_host",
        "help": "server bind address",
    },
    {
        "name": "--port",
        "default": 4000,
        "dest": "server_port",
        "help": "server port number",
    },
]


class CLITask:
    """Task base class."""

    _name = "invalid"
    _help = "invalid"
    _args: typing.List[typing.Dict[str, typing.Any]] = []

    classes: typing.List[typing.Type["CLITask"]] = []

    @classmethod
    def name(cls) -> str:
        """Get task cli name.

        Returns:
            name of the cli command

        """
        return cls._name

    @classmethod
    def args(cls) -> typing.List[typing.Dict[str, typing.Any]]:
        """Get arguments for this task.

        Returns:
            List of arguments

        """
        return cls._args

    @classmethod
    def help(cls) -> str:
        """Get help for this task.

        Returns:
            Help string

        """
        return cls._help

    def __init__(self, args: argparse.Namespace):
        """Initialize a task.

        Args:
            args: command line argument namespace

        """
        self._cli_args = args

    def run(self):
        """Run the task."""
        raise NotImplementedError(f"'{ self.__class__.__name__}' needs to override 'run' method.")

    def __init_subclass__(cls, **kwargs):
        """Store the new class when this class is subclassed."""
        super().__init_subclass__(**kwargs)
        CLITask.classes.append(cls)

    @classmethod
    def commands(cls) -> typing.List[typing.Type["CLITask"]]:
        """Get all available CLI tasks.

        Returns:
            Dictionary containing all CLI tasks

        """
        return CLITask.classes

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CLITask":
        """Crete a task object by using command line arguments.

        Args:
            args: command line arguments

        """
        command_dict = {command.name(): command for command in CLITask.classes}

        # check if command is valid
        if args.command not in command_dict:
            raise ValueError(f"'{args.command}' is not a valid command.")

        # create and return task object
        return command_dict[args.command](args)


class StartServerCLITask(CLITask):
    """Task class to start a command server."""

    _name = "start_server"
    _help = "start secssim server"
    _args = SERVER_ARGS

    def run(self):
        """Run the start server task."""
        # fork intermediate process
        pid = os.fork()

        # exit if we are the parent process
        if not pid == 0:
            sys.exit()

        # setup child process
        os.setsid()
        os.umask(0)

        # fork child process
        pid2 = os.fork()

        # exit if we are the intermediate process
        if not pid2 == 0:
            sys.exit()  # First child exists

        # start command server
        secsgem_simulator.command_server.CommandServer(self._cli_args.server_host, self._cli_args.server_port).start()


class RunServerCLITask(CLITask):
    """Task class to start a command server."""

    _name = "run_server"
    _help = "run secssim server"
    _args = SERVER_ARGS

    def run(self):
        """Run command server."""
        secsgem_simulator.command_server.CommandServer(self._cli_args.server_host, self._cli_args.server_port).start()


class PingServerCLITask(CLITask):
    """Task class to ping the server."""

    _name = "ping_server"
    _help = "ping secssim server"
    _args = SERVER_ARGS

    def run(self):
        """Run the ping server task."""
        # connect to task server
        address = (self._cli_args.server_host, self._cli_args.server_port)
        conn = multiprocessing.connection.Client(address)

        ping_message = secsgem_simulator.command_server.ServerMessage("ping")

        # send the terminate command
        conn.send(ping_message.to_message())

        print(conn.recv()["message"])

        close_message = secsgem_simulator.command_server.ServerMessage("close")

        # send the terminate command
        conn.send(close_message.to_message())

        # disconnect
        conn.close()


class StopServerCLITask(CLITask):
    """Task class to start a command server."""

    _name = "stop_server"
    _help = "stop secssim server"
    _args = SERVER_ARGS

    def run(self):
        """Run the stop server task."""
        # connect to task server
        address = (self._cli_args.server_host, self._cli_args.server_port)
        conn = multiprocessing.connection.Client(address)

        terminate_message = secsgem_simulator.command_server.ServerMessage("terminate")

        # send the terminate command
        conn.send(terminate_message.to_message())

        print(conn.recv())

        # disconnect
        conn.close()


class RunScriptCLITask(CLITask):
    """Task class to run a lua script."""

    _name = "run_script"
    _help = "run secssim script"
    _args = [
        {
            "name": "script_name",
            "help": "lua script name",
        },
    ]

    def run(self):
        """Run script."""
        runner = secsgem_simulator.script_runner.ScriptRunner()
        response = runner.run_string(pathlib.Path(self._cli_args.script_name).read_text(encoding="utf8"))
        print(response)
