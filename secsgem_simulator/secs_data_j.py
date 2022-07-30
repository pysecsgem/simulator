"""JIS8 based string SECS data."""
import string
import typing

from secsgem_simulator.secs_data import SECSData, PacketData
from secsgem_simulator.sml_parser import SMLParser


class SECSDataJ(SECSData):
    """SECS jis8 string data type wrapper."""

    _sml_type = "J"
    _hsms_type = 0o21
    _minimum_value = 0
    _maximum_value = 0xFF

    printable_chars = string.printable.replace("\n", "").replace("\r", "").encode('latin1')

    def validate_value(self, value: typing.Union[str, bytes]) -> str:
        """Validate the input value and return possibly converted value.

        Args:
            value: passed value

        Returns:
            converted value

        """
        if not isinstance(value, (str, bytes)):
            raise Exception

        return value

    @classmethod
    def _read_sml_token(cls, parser: SMLParser) -> bytes:
        data = b""

        while parser.peek_token().value != ">":
            item = parser.get_token()

            if item.value.startswith('"'):
                data += item.value.strip('"').encode("ascii")
            else:
                char = int(item.value, 0)
                char = int(cls._verify_value_in_bounds(char, item))
                data += bytes([char])

        parser.get_token()

        return data

    def to_sml(self, indent=0):
        """Convert data object to SML string.

        Args:
            indent: indent level in spaces

        Returns:
            SML text

        """
        data = ""
        last_char_printable = False

        for char in self._value:
            output = char
            if char in self.printable_chars:
                if last_char_printable:
                    data += chr(output)
                else:
                    data += ' "' + chr(output)
                last_char_printable = True
            else:
                if last_char_printable:
                    data += '" ' + hex(output)
                else:
                    data += ' ' + hex(output)
                last_char_printable = False

        if last_char_printable:
            data += '"'

        return f"{indent * ' '}< {self._sml_type}{data}>"

    def encode(self) -> bytes:
        """Encode the data value to transmittable bytes.

        Return:
            byte array of data

        """
        result = self.encode_item_header(len(self._value))

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

        return cls(data.get(length))
