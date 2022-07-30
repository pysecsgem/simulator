"""Specific simulator plugin for secsgem 0.1."""
import importlib
import pathlib
import random
import threading
import time
import types
import typing

from secsgem_simulator.secsgem_package_base import SecsgemPackage, HSMSSType, ScriptHSMSConnection
from secsgem_simulator.secs_data import SECSFunction


class SecsgemPackage01(SecsgemPackage):
    """Wrapper class for the secsgem package."""

    def __init__(self, package_path: pathlib.Path):
        """Initialize a secsgem package from the package path.

        Args:
            package_path: path of the packages site-packages

        """
        super().__init__(package_path)
        self._modules: typing.Dict[str, types.ModuleType] = {}

    @staticmethod
    def _load_module(module_name: str) -> types.ModuleType:
        """Load a module for the package.

        Args:
            module_name: name of the module

        Returns:
            loaded module

        """
        # import / reload module
        module = importlib.import_module(module_name)
        importlib.reload(module)

        return module

    def module(self, name: str) -> types.ModuleType:
        """Get a module.

        The module will be loaded if it was not loaded before.

        Args:
            name: name of the module

        Returns:
            module with the passed name

        """
        if name not in self._modules:
            self._modules[name] = self._load_module(name)

        return self._modules[name]

    def hsms(self, address, port, active, session_id) -> ScriptHSMSConnection:
        """Initialize a hsms object for this package."""
        return ScriptHSMSConnection01(self, address, port, active, session_id)

    @classmethod
    def matches(cls, version: str) -> bool:
        """Check if this interface matches the passed version.

        Args:
            version: version number

        Returns:
            True if version matches

        """
        return version.startswith("0.1.")


class ScriptHSMSConnection01(ScriptHSMSConnection):  # pylint: disable=too-many-public-methods
    """HSMS connection."""

    def __init__(self,  # pylint: disable=too-many-arguments
                 module_loader: "SecsgemPackage",
                 address, port, active, session_id):
        """Initialize a hsms connection.

        Args:
            module_loader: object for loading modules
            address: address for the hsms connection
            port: port for the hsms connection
            active: is hsms connection active
            session_id: session id for hsms connection

        """
        self._module_loader = module_loader
        self._secsgem: typing.Any = module_loader.module("secsgem")

        self._responses: typing.List[typing.Any] = []
        self._response_lock = threading.Lock()

        if active:
            self._connection = self._secsgem.HsmsActiveConnection(address, port, session_id, self)
        else:
            self._connection = self._secsgem.HsmsPassiveConnection(address, port, session_id, self)

        self._wait_for_connection_event = threading.Event()
        self._wait_for_disconnection_event = threading.Event()

    def on_connection_established(self, _):
        """HSMS connection established event handler.

        This is called when a tcp/hsms connection is established
        """
        print("# connected")
        self._wait_for_connection_event.set()

    def on_connection_packet_received(self, _, packet):
        """HSMS connection packet received event handler.

        This is called when an hsms packet was received.

        Args:
            packet: received hsms packet

        """
        if packet.header.sType != 0:
            print(f"< {packet.header}\n  {HSMSSType.from_id(packet.header.sType)}")
        else:
            packet = SECSFunction.from_hsms_packet(packet)
            print(f"< {packet.hsms_header}\n  {packet}")

        with self._response_lock:
            self._responses.append(packet)

    def on_connection_closed(self, _):
        """HSMS connection closed event handler.

        This is called when the tcp/hsms connection was closed.
        """
        print("# disconnected")
        self._wait_for_disconnection_event.set()

    def connect(self):
        """Enable the connection."""
        self._connection.enable()

        self._wait_for_connection_event.wait()
        self._wait_for_connection_event.clear()

    def disconnect(self):
        """Disable the connection."""
        self._connection.disable()

        self._wait_for_disconnection_event.wait()
        self._wait_for_disconnection_event.clear()

    def send_select_req(self):
        """Send a select request."""
        system_id = random.randint(0, 0xFFFFFFFF)

        header = self._secsgem.HsmsSelectReqHeader(system_id)
        return self._send_packet(header)

    def wait_for_select_req(self):
        """Wait for a select request."""
        return self._wait_for_s_type(HSMSSType.from_name("Select.req"))

    def send_select_rsp(self, packet):
        """Send a select request."""
        header = self._secsgem.HsmsSelectRspHeader(packet.header.system)
        return self._send_packet(header)

    def wait_for_select_rsp(self):
        """Wait for a select request."""
        return self._wait_for_s_type(HSMSSType.from_name("Select.rsp"))

    def send_deselect_req(self):
        """Send a deselect request."""
        system_id = random.randint(0, 0xFFFFFFFF)

        header = self._secsgem.HsmsDeselectReqHeader(system_id)
        return self._send_packet(header)

    def wait_for_deselect_req(self):
        """Wait for a deselect request."""
        return self._wait_for_s_type(HSMSSType.from_name("Deselect.req"))

    def send_deselect_rsp(self, packet):
        """Send a deselect request."""
        header = self._secsgem.HsmsDeselectRspHeader(packet.header.system)
        return self._send_packet(header)

    def wait_for_deselect_rsp(self):
        """Wait for a deselect request."""
        return self._wait_for_s_type(HSMSSType.from_name("Deselect.rsp"))

    def send_linktest_req(self):
        """Send a linktest request."""
        system_id = random.randint(0, 0xFFFFFFFF)

        header = self._secsgem.HsmsLinktestReqHeader(system_id)
        return self._send_packet(header)

    def wait_for_linktest_req(self):
        """Wait for a linktest request."""
        return self._wait_for_s_type(HSMSSType.from_name("Linktest.req"))

    def send_linktest_rsp(self, packet):
        """Send a linktest request."""
        header = self._secsgem.HsmsLinktestRspHeader(packet.header.system)
        return self._send_packet(header)

    def wait_for_linktest_rsp(self):
        """Wait for a linktest request."""
        return self._wait_for_s_type(HSMSSType.from_name("Linktest.rsp"))

    def send_reject_req(self, packet, reason: int):
        """Send a reject request."""
        header = self._secsgem.HsmsRejectReqHeader(packet.header.system, packet.header.sType, reason)
        return self._send_packet(header)

    def wait_for_reject_req(self):
        """Wait for a reject request."""
        return self._wait_for_s_type(HSMSSType.from_name("Reject.req"))

    def send_separate_req(self):
        """Send a separate request."""
        system_id = random.randint(0, 0xFFFFFFFF)

        header = self._secsgem.HsmsSeparateReqHeader(system_id)
        return self._send_packet(header)

    def wait_for_separate_req(self):
        """Wait for a separate request."""
        return self._wait_for_s_type(HSMSSType.from_name("Separate.req"))

    def wait_for_packet_reply(self, packet):
        """Wait for reply for the passed package.

        Args:
            packet: packet to wait for reply to

        Returns:
            Reply packet

        """
        return self._wait_for_system_id(packet.header.system)

    def send_function(self, sml: str, packet=None):
        """Send a stream/function from sml text.

        Args:
            sml: SML text to parse function from
            packet: source packet to answer

        """
        if packet is not None:
            system = packet.hsms_header.system
        else:
            system = random.randint(0, 0xFFFFFFFF)

        function = SECSFunction.from_sml(sml)
        header = self._secsgem.HsmsStreamFunctionHeader(system, function.stream, function.function, function.w_bit, 0)

        self._send_packet(header, function)

    def wait_for_function(self, stream: int, function: int):
        """Wait for reply for the passed package.

        Args:
            stream: stream to wait for
            function: function to wait for

        Returns:
            Received packet

        """
        return self._wait_for_function(stream, function)

    def _send_packet(self, header, function: SECSFunction = None):
        """Send a hsms packet."""
        if function is not None and function.data is not None:
            packet = self._secsgem.HsmsPacket(header, function.data.encode())
        else:
            packet = self._secsgem.HsmsPacket(header)

        if packet.header.sType > 0:
            print(f"> {packet.header}\n  {HSMSSType.from_id(packet.header.sType)}")
        else:
            print(f"> {packet.header}\n {function}")

        if not self._connection.send_packet(packet):
            return None

        return packet

    def _wait_for_condition(self, condition: typing.Callable, timeout: float = 5.0, wait: float = 0.25) -> typing.Any:
        """Wait until condition is met or timeout occurs.

        Args:
            condition: condition function
            timeout: time to wait for system id
            wait: waiting time between checks

        Returns:
            Result package

        """
        timeout_end = time.time() + timeout
        while time.time() < timeout_end:
            with self._response_lock:
                result = condition()
                if result is not None:
                    self._responses.remove(result)
                    return result

            time.sleep(wait)
        raise Exception("Reply not received within timeout.")

    def _wait_for_system_id(self, system_id: int, timeout: float = 5.0, wait: float = 0.25) -> typing.Any:
        """Wait until system id is present in responses.

        Args:
            system_id: system id to wait for
            timeout: time to wait for system id
            wait: waiting time between checks

        Returns:
            False when system id did not show up within timeout

        """
        def _condition():
            return next((packet for packet in self._responses if packet.header.system == system_id), None)

        return self._wait_for_condition(_condition, timeout, wait)

    def _wait_for_s_type(self, s_type: int, timeout: float = 5.0, wait: float = 0.25) -> typing.Any:
        """Wait until s type is present in responses.

        Args:
            s_type: system id to wait for
            timeout: time to wait for system id
            wait: waiting time between checks

        Returns:
            False when system id did not show up within timeout

        """
        def _condition():
            return next((packet for packet in self._responses if packet.header.sType == s_type), None)

        return self._wait_for_condition(_condition, timeout, wait)

    def _wait_for_function(self, stream: int, function: int, timeout: float = 5.0, wait: float = 0.25) -> typing.Any:
        """Wait until s type is present in responses.

        Args:
            stream: stream to wait for
            function: function to wait for
            timeout: time to wait for system id
            wait: waiting time between checks

        Returns:
            False when system id did not show up within timeout

        """
        def _condition():
            return next((packet for packet in self._responses
                         if packet.hsms_header.stream == stream
                         and packet.hsms_header.function == function),
                        None)

        return self._wait_for_condition(_condition, timeout, wait)

    def extra_packets(self):
        """Print out the packets in the receive queue."""
        with self._response_lock:
            return self._responses.copy()
