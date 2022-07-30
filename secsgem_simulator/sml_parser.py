"""SML parser."""
import io


class SMLParseError(BaseException):
    """Exception class for SML parse error."""

    def __init__(self, message: str, token: "SMLToken"):
        """Initialize parse error exception.

        Args:
            message: exception message
            token: token the error occurred in

        """
        super().__init__(message)

        self.token = token


class SMLToken:
    """SML token representation."""

    def __init__(self, value: str, line: int, col: int, parser: "SMLParser"):
        """Initialize an SML token.

        Args:
            value: token
            line: line in source code
            col: column in source code
            parser: parser that generated this token

        """
        self._value = value
        self._line = line
        self._col = col
        self._parser = parser

    @property
    def value(self) -> str:
        """Get the value property.

        Returns:
              token value

        """
        return self._value

    @property
    def line(self) -> int:
        """Get the line property.

        Returns:
              token line

        """
        return self._line

    @property
    def col(self) -> int:
        """Get the col property.

        Returns:
              token col

        """
        return self._col

    @property
    def parser(self) -> "SMLParser":
        """Get the parser property.

        Returns:
              token parser

        """
        return self._parser

    def __repr__(self):
        """Generate string representation of object."""
        return f"[{self.line:05d}|{self.col:05d}] {self.value}"

    def get_error(self, message: str) -> str:
        """Format a source code error output for this token.

        Args:
            message: error message

        Returns:
            formatted error message

        """
        line = self.line - 1
        prefix = (self.col - 1) * ' '
        result = f"{self.parser.source_line(line)}\n{prefix}^-- {message}"
        return result

    def exception(self, message: str) -> SMLParseError:
        """Raise exception for a source code error output for a token.

        Args:
            message: error message

        """
        return SMLParseError(f"\n{self.get_error(message)}", self)


class SMLParser:
    """SML structure parser."""

    whitespaces = " \t\n\r"
    operators = "<>[]"
    literal_delimiter = "'\""

    def __init__(self, source):
        """Initialize a SML parser.

        Args:
            source: IO object of the source code

        """
        if isinstance(source, str):
            source = io.StringIO(source)

        self._source = source

        self._line = 1
        self._col = 1

        self._source_lines = [""]

        self._tokens = []
        self._token_counter = -1

        self.parse_all()

    def source_line(self, line: int) -> str:
        """Get line of the source code.

        Args:
            line: line number of the code

        Returns:
            code line

        """
        return self._source_lines[line]

    def _get_char(self) -> str:
        char = self._source.read(1)

        self._col += 1

        if char == "\n":
            self._source_lines.append("")
            self._line += 1
            self._col = 0
        elif char == "\r":
            self._col = 0
        else:
            self._source_lines[-1] = self._source_lines[-1] + char

        return char

    def parse_all(self):
        """Parse all tokens in the source code."""
        current_token = ""
        location = _SMLParserLocation()
        current_delimiter = ""

        while True:
            char = self._get_char()

            location.update_uninitialized_line(self._line)
            location.update_uninitialized_column(self._col)

            if char == '':
                return

            if current_delimiter:
                if char == current_delimiter:
                    current_token += char
                    if current_token:
                        self._tokens.append(SMLToken(current_token, location.line, location.column, self))
                        current_token = ""
                    location.reset()
                    current_delimiter = ""
                    continue

                current_token += char
                continue

            if char in self.whitespaces:
                if current_token:
                    self._tokens.append(SMLToken(current_token, location.line, location.column, self))
                    current_token = ""
                location.reset()
                continue

            if char in self.operators:
                if current_token:
                    self._tokens.append(SMLToken(current_token, location.line, location.column, self))
                    current_token = ""
                self._tokens.append(SMLToken(char, self._line, self._col, self))
                location.reset()
                continue

            if char in self.literal_delimiter:
                current_delimiter = char

            current_token += char

    def get_token(self) -> SMLToken:
        """Get the next available token.

        Returns:
              next token

        """
        self._token_counter += 1
        return self._tokens[self._token_counter]

    def peek_token(self, ahead: int = 1) -> SMLToken:
        """Get an available token without incrementing the current position.

        Returns:
              token

        """
        return self._tokens[self._token_counter + ahead]


class _SMLParserLocation:
    def __init__(self, line: int = -1, column: int = -1):
        self._line = line
        self._column = column

    @property
    def line(self) -> int:
        """Get current parser line."""
        return self._line

    @property
    def column(self) -> int:
        """Get current parser column."""
        return self._line

    def reset_line(self):
        """Reset the line to uninitialized."""
        self._line = -1

    def reset_column(self):
        """Reset the column to uninitialized."""
        self._column = -1

    def reset(self):
        """Reset line and column to uninitialized."""
        self.reset_line()
        self.reset_column()

    def update_uninitialized_line(self, line: int):
        """Update the line if it is uninitialized."""
        if self._line == -1:
            self._line = line

    def update_uninitialized_column(self, column: int):
        """Update the column if it is uninitialized."""
        if self._column == -1:
            self._column = column
