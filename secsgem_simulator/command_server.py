"""Server for remote management of simulation."""
import multiprocessing.connection
import traceback
import typing

from secsgem_simulator.server_tasks import ServerTask


class ServerMessage:
    """Container for message from client to server."""

    def __init__(self, message: str, data: typing.Dict[str, typing.Any] = None):
        """Create a message object.

        Args:
            message: message string
            data: extra message data

        """
        self._message = message
        self._data = data if data is not None else {}

    @property
    def message(self) -> str:
        """Get message name.

        Returns:
            message name

        """
        return self._message

    @property
    def data(self) -> typing.Dict[str, typing.Any]:
        """Get the data connected to the message.

        Returns:
            message data

        """
        return self._data

    def to_message(self) -> typing.Tuple[str, typing.Dict[str, typing.Any]]:
        """Generate a transferable message.

        Returns:
            message to send over the connection

        """
        return self._message, self._data

    @classmethod
    def from_message(cls, message: typing.Tuple[str, typing.Dict[str, typing.Any]]):
        """Create a ServerMessage object from a message received from a connection.

        Args:
            message: received message

        """
        return cls(message[0], message[1])


class CommandServer:  # pylint: disable=too-few-public-methods
    """SECS/GEM simulator command server."""

    def __init__(self, host: str, port: int):
        """Initialize the command server object.

        Args:
            host: bind address/hostname
            port: bind port

        """
        self.host = host
        self.port = port

    def start(self):
        """Start the command server."""
        address = (self.host, self.port)

        with multiprocessing.connection.Listener(address) as listener:
            print(f"server listening on '{address}'")
            self._handle_connections(listener)

    def _handle_connections(self, listener: multiprocessing.connection.Listener):
        """Accept incoming connections.

        Args:
            listener: connection listener

        """
        while True:
            with listener.accept() as conn:
                print(f"connection accepted from '{listener.last_accepted}'")

                if self._handle_connection(conn) is True:
                    return True

    def _handle_connection(self, connection: multiprocessing.connection._ConnectionBase) -> bool:
        """Process a single connection.

        Args:
            connection: connected client connection

        Returns:
            True if listener should be terminated

        """
        while True:
            message = ServerMessage.from_message(connection.recv())

            task = ServerTask.task_from_message(message, self, connection)

            try:
                result = task.run()
                connection.send(result.data)
            except BaseException as exc:  # pylint: disable=broad-except
                connection.send({"error": str(exc), "stack": traceback.format_exc()})
                traceback.print_exc()
                continue

            if result.terminate:
                connection.close()
                return True

            if result.close:
                connection.close()
                return False
