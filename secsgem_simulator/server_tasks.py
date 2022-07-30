"""Tasks for remote server."""
import multiprocessing.connection
import typing

from secsgem_simulator import script_runner

if typing.TYPE_CHECKING:
    from secsgem_simulator.command_server import ServerMessage, CommandServer


class ServerTaskResult:  # pylint: disable=too-few-public-methods
    """Result data for server task."""

    def __init__(self, data: typing.Dict[str, typing.Any] = None, close: bool = False, terminate: bool = False):
        """Initialize server task result object.

        Args:
            data: result to return to client
            close: close the connection after this task
            terminate: terminate the server after this task

        """
        self.data = data if data is not None else {}
        self.close = close
        self.terminate = terminate


class ServerTask:
    """Server task base class."""

    _command = "invalid"

    classes: typing.List[typing.Type["ServerTask"]] = []

    def __init__(self,
                 message: "ServerMessage",
                 server: "CommandServer",
                 connection: multiprocessing.connection._ConnectionBase):
        """Initialize a server task object.

        Args:
            message: message received for this task
            server: server the task command was started from
            connection: connection for the command

        """
        self._message = message
        self._server = server
        self._connection = connection

    def __init_subclass__(cls, **kwargs):
        """Store the new class when this class is subclassed."""
        super().__init_subclass__(**kwargs)
        ServerTask.classes.append(cls)

    @classmethod
    def task_from_message(
            cls,
            msg: "ServerMessage",
            server: "CommandServer",
            connection: multiprocessing.connection._ConnectionBase) -> "ServerTask":
        """Return a task object for a message."""
        tasks = {task.command(): task for task in ServerTask.classes}

        if msg.message not in tasks:
            raise NotImplementedError(f"Unknown message command '{msg.message}'")

        return tasks[msg.message](msg, server, connection)

    @classmethod
    def command(cls) -> str:
        """Get the command name of the task.

        Returns:
            command name

        """
        return cls._command

    def run(self) -> ServerTaskResult:
        """Run the task."""
        raise NotImplementedError(f"{self.__class__.__name__} does not have a 'run' implementation")


class TerminateServerTask(ServerTask):
    """Terminate server task class."""

    _command = "terminate"

    def run(self) -> ServerTaskResult:
        """Run the task."""
        return ServerTaskResult(terminate=True)


class CloseServerTask(ServerTask):
    """Close server task class."""

    _command = "close"

    def run(self) -> ServerTaskResult:
        """Run the task."""
        return ServerTaskResult(close=True)


class PingServerTask(ServerTask):
    """Ping server task class."""

    _command = "ping"

    def run(self) -> ServerTaskResult:
        """Run the task."""
        return ServerTaskResult(data={"message": "pong"})


class RunScriptServerTask(ServerTask):
    """Run script server task class."""

    _command = "script"

    def run(self) -> ServerTaskResult:
        """Run the task."""
        runner = script_runner.ScriptRunner()

        result = runner.run_string(self._message.data["script"])
        return ServerTaskResult(data={"result": result})
