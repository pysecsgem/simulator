"""Secs data classes."""
import abc
import re
import typing

from secsgem_simulator.sml_parser import SMLToken, SMLParser


class PacketData:
    """Wrapper for package data that allows moving over the data."""

    def __init__(self, data: bytes):
        """Initialize packet data.

        Args:
            data: packet raw data

        """
        self._data = data

    def peek(self) -> int:
        """Get the next packet byte without incrementing the pointer.

        Returns:
            requested data

        """
        return self._data[0]

    def get_one(self) -> int:
        """Get one packet byte.

        Returns:
            single packet byte

        """
        result = self._data[0]

        self._data = self._data[1:]

        return result

    def get(self, length: int = 1) -> bytes:
        """Get the next packet bytes.

        Args:
            length: number of bytes

        Returns:
            requested data

        """
        result = self._data[:length]

        self._data = self._data[length:]

        return result


class SECSData(abc.ABC):
    """SECS item data element."""

    _sml_type = ""
    _hsms_type = -1

    _minimum_value: typing.Union[int, float] = -0xFFFFFFFFFFFF
    _maximum_value: typing.Union[int, float] = -0xFFFFFFFFFFFF

    subclasses_by_sml: typing.Dict[str, typing.Type["SECSData"]] = {}
    subclasses_by_hsms: typing.Dict[int, typing.Type["SECSData"]] = {}

    def __init__(self, value: typing.Any):
        """Initialize data element.

        Args:
            value: new value for the element

        """
        self._import_inherited()
        self._value = self.validate_value(value)

    def __init_subclass__(cls, **kwargs):
        """Initialize a new sub-class."""
        super().__init_subclass__(**kwargs)
        if cls._sml_type is not None:
            cls.subclasses_by_sml[cls._sml_type.upper()] = cls
            cls.subclasses_by_hsms[cls._hsms_type] = cls

    @staticmethod
    def _import_inherited():
        import secsgem_simulator.secs_data_l  # pylint: disable=cyclic-import,import-outside-toplevel
        import secsgem_simulator.secs_data_b  # pylint: disable=cyclic-import,import-outside-toplevel
        import secsgem_simulator.secs_data_boolean  # pylint: disable=cyclic-import,import-outside-toplevel
        import secsgem_simulator.secs_data_a  # pylint: disable=cyclic-import,import-outside-toplevel
        import secsgem_simulator.secs_data_j  # pylint: disable=cyclic-import,import-outside-toplevel
        import secsgem_simulator.secs_data_number  # pylint: disable=cyclic-import,import-outside-toplevel

        return (secsgem_simulator.secs_data_l,
                secsgem_simulator.secs_data_b,
                secsgem_simulator.secs_data_boolean,
                secsgem_simulator.secs_data_a,
                secsgem_simulator.secs_data_j,
                secsgem_simulator.secs_data_number)

    def __repr__(self) -> str:
        """Generate string representation of object."""
        return self.to_sml()

    def to_sml(self, indent=0) -> str:
        """Convert data object to SML string.

        Args:
            indent: indent level in spaces

        Returns:
            SML text

        """
        if len(self._value) == 0:
            return f"{indent * ' '}< {self._sml_type} >"

        values_string = " ".join([self._format_value(value) for value in self._value])
        return f"{indent * ' '}< {self._sml_type} {values_string} >"

    @staticmethod
    def _format_value(value: typing.Any) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def validate_value(self, value: typing.Any) -> typing.Any:
        """Validate the input value and return possibly converted value.

        Args:
            value: passed value

        Returns:
            converted value

        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _read_sml_token(cls, parser: SMLParser) -> typing.Any:
        return cls._read_item(parser)

    @abc.abstractmethod
    def encode(self) -> bytes:
        """Encode the data value to transmittable bytes.

        Return:
            byte array of data

        """
        raise NotImplementedError()

    @classmethod
    def _decode_peek_item_type(cls, data: PacketData):
        return (data.peek() & 0b11111100) >> 2

    @classmethod
    def _decode_item_header(cls, data: PacketData) -> typing.Tuple[int, int]:
        # parse format byte
        format_byte = data.get_one()

        format_code = (format_byte & 0b11111100) >> 2
        length_bytes = (format_byte & 0b00000011)

        # read 1-3 length bytes
        length = 0
        for _ in range(length_bytes):
            length <<= 8
            length += data.get_one()

        return format_code, length

    @classmethod
    @abc.abstractmethod
    def decode(cls, data: PacketData) -> "SECSData":
        """Create a new data object by decoding a secs packet.

        Args:
            data: packet data

        Returns:
            new data object

        """
        cls._import_inherited()

        data_type = cls._decode_peek_item_type(data)

        if data_type not in cls.subclasses_by_hsms:
            raise Exception(f"Unknown data type '{data_type}'")

        return cls.subclasses_by_hsms[data_type].decode(data)

    @classmethod
    def from_sml_tokens(cls, parser: SMLParser) -> "SECSData":
        """Create a new data object from parsed sml data.

        Args:
            parser: sml parser

        Returns:
            new data object

        """
        cls._import_inherited()

        if cls is SECSData:
            return cls._read_sml_token(parser)

        if cls is cls.subclasses_by_sml["L"]:
            return cls(cls._read_items(parser, cls._read_sml_token))

        return cls(cls._read_sml_token(parser))

    @classmethod
    def _read_item(cls, parser: SMLParser) -> "SECSData":
        start_char = parser.get_token()

        if start_char.value != "<":
            raise start_char.exception(f"expected open character '<', found '{start_char.value}'")

        data_type = parser.get_token()

        if data_type.value.upper() not in cls.subclasses_by_sml:
            raise data_type.exception(f"unknown data type '{data_type.value}'")

        return cls.subclasses_by_sml[data_type.value.upper()].from_sml_tokens(parser)

    @classmethod
    def _read_length(cls, parser: SMLParser):
        length = parser.get_token()

        closing = parser.get_token()
        if closing.value != "]":
            raise closing.exception(f"expected length close ']', got '{closing.value}''")

        return length

    @classmethod
    def _read_items(cls, parser: SMLParser, sub_parser: typing.Callable):
        items = []
        length = None
        count = 0

        if parser.peek_token().value == "[":
            parser.get_token()
            length = cls._read_length(parser)

        while parser.peek_token().value not in ">.":
            items.append(sub_parser(parser))
            count += 1

        parser.get_token()

        if length is not None and 0 < int(length.value) != count:
            raise length.exception(f"expected length ({length.value}) doesn't match counted items ({count})")

        return items

    def encode_item_header(self, length: int) -> bytes:
        """Encode item header depending on the number of length bytes required.

        Args:
            length: number of bytes in data

        Returns:
            encoded item header bytes

        """
        if length < 0:
            raise ValueError(f"Encoding {self.__class__.__name__} not possible, data length too small {length}")
        if length > 0xFFFFFF:
            raise ValueError(f"Encoding {self.__class__.__name__} not possible, data length too big {length}")

        if length > 0xFFFF:
            length_bytes = 3
            format_byte = (self._hsms_type << 2) | length_bytes
            return bytes(bytearray((format_byte, (length & 0xFF0000) >> 16, (length & 0x00FF00) >> 8,
                                    (length & 0x0000FF))))
        if length > 0xFF:
            length_bytes = 2
            format_byte = (self._hsms_type << 2) | length_bytes
            return bytes(bytearray((format_byte, (length & 0x00FF00) >> 8, (length & 0x0000FF))))

        length_bytes = 1
        format_byte = (self._hsms_type << 2) | length_bytes
        return bytes(bytearray((format_byte, (length & 0x0000FF))))

    @classmethod
    def _verify_value_in_bounds(cls,
                                value: typing.Union[int, float],
                                item: typing.Optional[SMLToken] = None) -> typing.Union[int, float]:
        if cls._minimum_value <= value <= cls._maximum_value:
            return value

        if item is not None:
            raise item.exception(
                f"value '{item.value}' out of bounds for {cls._sml_type} ({cls._minimum_value} - {cls._maximum_value})")

        raise ValueError(
            f"value '{value}' out of bounds for {cls._sml_type} ({cls._minimum_value} - {cls._maximum_value})")

    @classmethod
    def _invalid_type_exception(cls, data: typing.Any) -> Exception:
        raise Exception(f"Invalid value '{data}' of '{data.__class__.__name__}' for '{cls.__name__}'")


class SECSFunction:
    """Representation of a secs stream function."""

    stream_function_regex = re.compile(r"^[sS](\d*)[fF](\d*)$")

    def __init__(self, stream: int, function: int, w_bit: bool, data: typing.Optional[SECSData], header=None):
        """Initialize a secs stream/function.

        Args:
            stream: stream number
            function: function number
            w_bit: answer request
            data: message data
            header: hsms header data

        """
        self.stream = stream
        self.function = function
        self.w_bit = w_bit
        self.data = data
        self.hsms_header = header

    def __repr__(self):
        """Generate a textual representation of an object."""
        return f"S{self.stream}F{self.function} {'W' if self.w_bit else ''}\n" \
               f"{self.data.to_sml(4) if self.data else ''} ."

    @classmethod
    def from_sml(cls, text: str):
        """Create a SECSFunction object from SML text.

        Args:
            text: SML text

        Returns:
            generated SECSFunction

        """
        tokens = SMLParser(text)

        stream_function_token = tokens.get_token()
        stream_function_match = cls.stream_function_regex.match(stream_function_token.value)

        if stream_function_match is None:
            raise stream_function_token.exception(
                f"expected stream function descriptor SxxFyy, found '{stream_function_token}")

        stream = int(stream_function_match.group(1))
        function = int(stream_function_match.group(2))

        w_bit = False
        if tokens.peek_token().value.lower() == "w":
            tokens.get_token()
            w_bit = True

        if tokens.peek_token().value == ".":
            return cls(stream, function, w_bit, None)

        data = SECSData.from_sml_tokens(tokens)

        final_token = tokens.get_token()
        if final_token.value != ".":
            raise final_token.exception(f"expected final character '.', found '{final_token.value}'")

        return cls(stream, function, w_bit, data)

    @classmethod
    def from_hsms_packet(cls, packet) -> "SECSFunction":
        """Create a SECSFunction object from a received packet.

        Args:
            packet: received packet

        Returns:
            generated SECSFunction

        """
        return cls(
            packet.header.stream,
            packet.header.function,
            packet.header.requireResponse,
            SECSData.decode(PacketData(packet.data)),
            packet.header
        )
