"""Base classes for version specific secsgem implementations."""
import abc
import pathlib
import types


class HSMSSType:
    """HSMS s-type mapper."""

    hsms_s_types = {
        1: "Select.req",
        2: "Select.rsp",
        3: "Deselect.req",
        4: "Deselect.rsp",
        5: "Linktest.req",
        6: "Linktest.rsp",
        7: "Reject.req",
        9: "Separate.req"
    }

    @classmethod
    def from_name(cls, name: str) -> int:
        """Get HSMS type id from name.

        Args:
            name: type name

        Returns:
            type id

        """
        for type_id, type_name in cls.hsms_s_types.items():
            if name.upper() == type_name.upper():
                return type_id

        return -1

    @classmethod
    def from_id(cls, identifier: int) -> str:
        """Get HSMS type name from id.

        Args:
            identifier: type id

        Returns:
            type name

        """
        return cls.hsms_s_types[identifier]


class ScriptHSMSConnection(abc.ABC):  # pylint: disable=too-many-public-methods
    """HSMS connection base class."""

    @abc.abstractmethod
    def on_connection_established(self, _):
        """HSMS connection established event handler."""
        raise NotImplementedError()

    @abc.abstractmethod
    def on_connection_packet_received(self, _, packet):
        """HSMS connection packet received event handler."""
        raise NotImplementedError()

    @abc.abstractmethod
    def on_connection_closed(self, _):
        """HSMS connection closed event handler."""
        raise NotImplementedError()

    @abc.abstractmethod
    def connect(self):
        """Enable the connection."""
        raise NotImplementedError()

    @abc.abstractmethod
    def disconnect(self):
        """Disable the connection."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_select_req(self):
        """Send a select request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_select_req(self):
        """Wait for a select request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_select_rsp(self, packet):
        """Send a select request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_select_rsp(self):
        """Wait for a select request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_deselect_req(self):
        """Send a deselect request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_deselect_req(self):
        """Wait for a deselect request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_deselect_rsp(self, packet):
        """Send a deselect request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_deselect_rsp(self):
        """Wait for a deselect request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_linktest_req(self):
        """Send a linktest request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_linktest_req(self):
        """Wait for a linktest request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_linktest_rsp(self, packet):
        """Send a linktest request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_linktest_rsp(self):
        """Wait for a linktest request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_reject_req(self, packet, reason: int):
        """Send a reject request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_reject_req(self):
        """Wait for a reject request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def send_separate_req(self):
        """Send a separate request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_separate_req(self):
        """Wait for a separate request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def wait_for_packet_reply(self, packet):
        """Wait for reply for the passed package."""
        raise NotImplementedError()

    @abc.abstractmethod
    def extra_packets(self):
        """Print out the packets in the receive queue."""
        raise NotImplementedError()


class SecsgemPackage(abc.ABC):
    """Wrapper class for the secsgem package."""

    @abc.abstractmethod
    def __init__(self, package_path: pathlib.Path):
        """Initialize a secsgem package from the package path.

        Args:
            package_path: path of the packages site-packages

        """
        self._package_path = package_path

    @abc.abstractmethod
    def module(self, name: str) -> types.ModuleType:
        """Get a module.

        The module will be loaded if it was not loaded before.

        Args:
            name: name of the module

        Returns:
            module with the passed name

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def hsms(self, address, port, active, session_id) -> ScriptHSMSConnection:
        """Initialize a hsms object for this package."""
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def matches(cls, version: str) -> bool:
        """Check if this interface matches the passed version.

        Args:
            version: version number

        Returns:
            True if version matches

        """
        raise NotImplementedError()
