from debug import *
from helper import *
from tokens import *


def insert_substrings(original_string, substring1, position1, substring2, position2):
    return (
        original_string[:position1]
        + substring1
        + original_string[position1:position2]
        + substring2
        + original_string[position2:]
    )


class CodeError(Exception):
    def __init__(
        self,
        message,
        error_code,
        error_token=None,
        start_position=None,
        end_position=None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.token = error_token or get_current_token()
        self.start_position = start_position or self.token["start_position"]
        self.end_position = end_position or self.token["end_position"]
        self.line_number = self.token["line_number"]
        self.line_position = line_start_positions[self.line_number - 1]
        self.line = lines[self.line_number - 1]
        self.relative_start_position = self.start_position - self.line_position
        self.relative_end_position = self.end_position - self.line_position
        self.start_token = [
            t for t in tokens if t["start_position"] <= self.start_position
        ][-1]
        self.end_token = [t for t in tokens if t["end_position"] >= self.end_position][
            0
        ]
        self.lines = lines[
            self.start_token["line_number"] - 1 : self.end_token["line_number"]
        ]


def display_error(e):
    error_line_numbers = range(
        e.start_token["line_number"], e.end_token["line_number"] + 1
    )
    line_number_digits = len(str(error_line_numbers[-1]))
    max_line_width = max(len(line) for line in e.lines)
    display_lines = [line.ljust(max_line_width) for line in e.lines]

    if e.token:
        underline_start_position = e.token["start_position"]
        underline_end_position = e.token["end_position"]
    else:
        underline_start_position = e.start_position
        underline_end_position = e.end_position

    underline_start_line_number = find_line_number(underline_start_position)
    underline_end_line_number = find_line_number(underline_end_position)
    relative_underline_start_position = (
        underline_start_position - line_start_positions[underline_start_line_number - 1]
    )
    relative_underline_end_position = (
        underline_end_position - line_start_positions[underline_end_line_number - 1] + 1
    )

    relative_underline_start_line_number = (
        underline_start_line_number - error_line_numbers[0]
    )
    relative_underline_end_line_number = (
        underline_end_line_number - error_line_numbers[0]
    )

    if relative_underline_start_line_number == relative_underline_end_line_number:
        display_lines[relative_underline_start_line_number] = insert_substrings(
            display_lines[relative_underline_start_line_number],
            "\033[4m",
            relative_underline_start_position,
            "\033[24m",
            relative_underline_end_position,
        )
    else:
        display_lines[relative_underline_start_line_number] = insert_substrings(
            display_lines[relative_underline_start_line_number],
            "\033[4m",
            relative_underline_start_position,
            "",
            relative_underline_start_position,
        )

        print("\033[0m", end="")

        display_lines[relative_underline_end_line_number] = insert_substrings(
            display_lines[relative_underline_end_line_number],
            "\033[24m",
            relative_underline_end_position,
            "",
            relative_underline_end_position,
        )

    for i, (line, line_number) in enumerate(zip(display_lines, error_line_numbers)):
        if line_number == underline_start_line_number:
            display_lines[i] = line + "\033[24m"

        if (
            line_number > underline_start_line_number
            and line_number < underline_end_line_number
        ):
            line = (
                "\033[4m"
                + line.strip()
                + "\033[24m"
                + " " * (max_line_width - len(line.strip()))
            )
            display_lines[i] = line

        if (
            line_number == underline_end_line_number
            and line_number != underline_start_line_number
        ):
            display_lines[i] = "\033[4m" + line

    if len(error_line_numbers) == 1:
        print(f"\033[31mError at line {e.line_number}: {e}\033[0m")
    else:
        print(
            f"\033[31mError from line {error_line_numbers[0]} to {error_line_numbers[-1]}: {e}\033[0m"
        )
    print("\033[31m", end="")
    print(f"╭─{"─" * line_number_digits}─┬─{"─" * max_line_width}─╮")
    for line, line_number in zip(display_lines, error_line_numbers):
        if DEBUG_SHOW_RAW_ERROR:
            print(
                f"\033[33m│ {str(line_number).ljust(line_number_digits)} │ {repr(line)} │\033[0m"
            )
        else:
            print(f"│ {str(line_number).ljust(line_number_digits)} │ {line} │")
    print(f"╰─{"─" * line_number_digits}─┴─{"─" * max_line_width}─╯")
    print("\033[0m", end="")

    print(f"\033[31mError code {e.error_code}\033[0m")
    print(
        f"\033[31m{CODE_FILE}:{e.line_number}:{relative_underline_start_position + 1}\033[0m"
    )

    if DEBUG_SHOW_ERROR_TOKEN:
        print("\033[33mDEBUG", e.token, "\033[0m")  