"""JIS8 based string SECS data."""
import string

from secsgem_simulator.secs_data_str import SECSDataStr


class SECSDataJ(SECSDataStr):
    """SECS jis8 string data type wrapper."""

    _sml_type = "J"
    _hsms_type = 0o21
    _encoding = "ascii"

    @classmethod
    def _char_coder(cls, char: int) -> bytes:
        return bytes([char])

    _minimum_value = 0
    _maximum_value = 0xFF

    printable_chars = string.printable.replace("\n", "").replace("\r", "").encode('latin1')
