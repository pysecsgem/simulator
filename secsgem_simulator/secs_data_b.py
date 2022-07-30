"""Byte SECS data."""
import typing

from secsgem_simulator.secs_data import SECSData, PacketData
from secsgem_simulator.sml_parser import SMLParser


class SECSDataB(SECSData):
    """SECS byte data type wrapper."""

    _sml_type = "B"
    _hsms_type = 0o10
    _minimum_value = 0
    _maximum_value = 0xFF

    def _validate_list_value(self, value: typing.Any) -> bytes:
        values = []
        for data_item in value:
            if isinstance(data_item, int):
                values.append(bytes(int(self._verify_value_in_bounds(data_item))))
            elif isinstance(data_item, bytes):
                values.append(data_item)
            else:
                raise self._invalid_type_exception(data_item)
        return b"".join(values)

    def validate_value(self, value: typing.Any) -> bytes:
        """Validate the input value and return possibly converted value.

        Args:
            value: passed value

        Returns:
            converted value

        """
        if isinstance(value, list):
            return self._validate_list_value(value)
        if isinstance(value, int):
            return bytes(int(self._verify_value_in_bounds(value)))
        if isinstance(value, bytes):
            return value

        raise self._invalid_type_exception(value)

    @classmethod
    def _read_sml_token(cls, parser: SMLParser) -> bytes:
        data = []

        while parser.peek_token().value != ">":
            item = parser.get_token()

            value = int(item.value, 0)
            value = int(cls._verify_value_in_bounds(value, item))
            data.append(value)

        parser.get_token()

        return bytes(data)

    @staticmethod
    def _format_value(value: int) -> str:
        return hex(value)

    def encode(self) -> bytes:
        """Encode the data value to transmittable bytes.

        Return:
            byte array of data

        """
        result = self.encode_item_header(len(self._value) if self._value is not None else 0)

        if self._value is not None:
            result += self._value

        return result

    @classmethod
    def decode(cls, data: PacketData) -> "SECSData":
        """Create a new data object by decoding a secs packet.

        Args:
            data: packet data

        Returns:
            new data object

        """
        _, length = cls._decode_item_header(data)

        return cls([data.get(length)])
