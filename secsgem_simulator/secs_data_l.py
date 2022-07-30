"""SECS data list."""
import typing

from secsgem_simulator.secs_data import SECSData, PacketData
from secsgem_simulator.sml_parser import SMLParser


class SECSDataL(SECSData):
    """SECS list data type wrapper."""

    _sml_type = "L"
    _hsms_type = 0o00

    def validate_value(self, value: typing.Any) -> typing.Any:
        """Validate the input value and return possibly converted value.

        Args:
            value: passed value

        Returns:
            converted value

        """
        if isinstance(value, list):
            return value

        raise Exception(f"Invalid value '{value}' for type '{self.__class__.__name__}'")

    @classmethod
    def _read_sml_token(cls, parser: SMLParser) -> SECSData:
        return cls._read_item(parser)

    def to_sml(self, indent=0):
        """Convert data object to SML string.

        Args:
            indent: indent level in spaces

        Returns:
            SML text

        """
        if len(self._value) == 0:
            return f"{indent * ' '}< {self._sml_type} >"

        values = [f"{value.to_sml(indent + 4)}" for value in self._value]
        values_text = '\n'.join(values)
        return f"{indent * ' '}< {self._sml_type} [{len(self._value)}]\n" \
               f"{values_text}\n" \
               f"{indent * ' '}>"

    def encode(self) -> bytes:
        """Encode the data value to transmittable bytes.

        Return:
            byte array of data

        """
        result = self.encode_item_header(len(self._value))

        for item in self._value:
            result += item.encode()

        return result

    @classmethod
    def decode(cls, data: PacketData) -> "SECSData":
        """Create a new data object by decoding a secs packet.

        Args:
            data: packet data

        Returns:
            new data object

        """
        (_, length) = cls._decode_item_header(data)

        items = []
        # list
        for _ in range(length):
            items.append(SECSData.decode(data))

        return cls(items)
