"""Latin 1 based string SECS data."""
import string

from secsgem_simulator.secs_data_str import SECSDataStr
from secsgem_simulator.sml_parser import SMLParser


class SECSDataA(SECSDataStr):
    """SECS latin1 string data type wrapper."""

    _sml_type = "A"
    _hsms_type = 0o20
    _encoding = "latin1"

    @classmethod
    def _char_coder(cls, char: int) -> bytes:
        return char.to_bytes(1, "big")

    _minimum_value = 0
    _maximum_value = 0xFF

    printable_chars = string.printable.replace("\n", "").replace("\r", "").encode('latin1')

