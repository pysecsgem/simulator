"""Boolean SECS data."""
import typing

from secsgem_simulator.secs_data import SECSData, PacketData
from secsgem_simulator.sml_parser import SMLParser


class SECSDataBOOLEAN(SECSData):
    """SECS boolean data type wrapper."""

    _sml_type = "BOOLEAN"
    _hsms_type = 0o11
    _minimum_value = 0
    _maximum_value = 1

    def _validate_list_value(self, value: typing.Any) -> typing.List[bool]:
        values = []
        for data_item in value:
            if isinstance(data_item, int):
                values.append(self._verify_value_in_bounds(data_item) == 1)
            elif isinstance(data_item, bool):
                values.append(data_item)
            else:
                raise self._invalid_type_exception(data_item)

        return values

    def validate_value(self, value: typing.Any) -> typing.List[bool]:
        """Validate the input value and return possibly converted value.

        Args:
            value: passed value

        Returns:
            converted value

        """
        if isinstance(value, list):
            return self._validate_list_value(value)
        if isinstance(value, int):
            return [self._verify_value_in_bounds(value) == 1]
        if isinstance(value, bool):
            return [value]

        raise self._invalid_type_exception(value)

    @classmethod
    def _read_sml_token(cls, parser: SMLParser) -> list[bool]:
        data = []

        while parser.peek_token().value != ">":
            item = parser.get_token()

            value = int(item.value, 0)
            value = int(cls._verify_value_in_bounds(value, item))
            data.append(value == 1)

        parser.get_token()

        return data

    @staticmethod
    def _format_value(value: bool) -> str:
        return "0x1" if value else "0x0"

    def encode(self) -> bytes:
        """Encode the data value to transmittable bytes.

        Return:
            byte array of data

        """
        result = self.encode_item_header(len(self._value))

        for counter, _ in enumerate(self._value):
            value = self._value[counter]
            if value:
                result += b"\1"
            else:
                result += b"\0"

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

        result = [char > 0 for char in data.get(length)]

        return cls(result)
