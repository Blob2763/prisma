from lex import tokenise
import re
from functions import *
from helper import *
from debug import *
from timeit import default_timer

start_time = default_timer()

CODE_FILE = "code.prsm"

tokens = tokenise("rules.lexif", CODE_FILE)
with open(CODE_FILE, "r") as file:
    code = file.read()
    lines = code.split("\n")
    line_start_positions = [0] + [m.end() for m in re.finditer("\n", code)]

num_tokens = len(tokens)
token_number = 0


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
        self.token = error_token or tokens[token_number]
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


def skip_to_non_ignore():
    global token_number
    while token_number < num_tokens and tokens[token_number]["class"] == "IGNORE":
        token_number += 1


def next_non_ignore():
    global token_number
    token_number += 1
    if token_number < num_tokens:
        skip_to_non_ignore()


def get_parameters():
    parameters = []
    current_parameter = []
    while not check_token_type(tokens[token_number], "DELIMITER", "RPAREN"):
        if check_token_type(tokens[token_number], "DELIMITER", "COMMA"):
            parameters.append(current_parameter)
            current_parameter = []
        else:
            current_parameter.append(tokens[token_number])
        next_non_ignore()

        if token_number >= num_tokens:
            raise CodeError(
                "Expected ')' at the end",
                error_code=1006,
                error_token=current_parameter[-1],
            )

    if current_parameter:
        parameters.append(current_parameter)

    num_parameters = len(parameters)

    return parameters, num_parameters


def get_function_tokens():
    l_paren_token = tokens[token_number]
    next_non_ignore()
    parameters, num_parameters = get_parameters()
    r_paren_token = tokens[token_number]

    return l_paren_token, parameters, num_parameters, r_paren_token


def get_keyword_tokens():
    keyword_tokens = []
    while not check_token_type(tokens[token_number], "DELIMITER", "SEMICOLON"):
        current_token = tokens[token_number]

        keyword_tokens.append(current_token)
        if (
            token_number >= num_tokens
            or current_token["class"] == "FUNCTION"
            or current_token["class"] == "KEYWORD"
            or current_token["class"] == "LOOP"
        ):
            raise CodeError(
                "Expected ';' at the end",
                error_code=1001,
                error_token=keyword_tokens[-2],
            )

        next_non_ignore()

    return keyword_tokens


def raise_code_error(fake_code_error):
    raise CodeError(
        fake_code_error,
        error_code=fake_code_error.error_code,
        error_token=fake_code_error.error_token,
    )


def safe_execute(func, parameters):
    try:
        return func(parameters)
    except FakeCodeError as e:
        raise_code_error(e)


def find_line_number(position):
    return len(
        [
            line_start_pos
            for line_start_pos in line_start_positions
            if line_start_pos <= position
        ]
    )


try:
    if check_token_type(tokens[-1], "ERROR", "UNFINISHED_TOKEN"):
        raise CodeError("Unfinished token", error_code=1003, error_token=tokens[-1])

    skip_to_non_ignore()
    while token_number < num_tokens:
        token = tokens[token_number]
        
        if DEBUG_ONLY_TOKENS:
            print(f"\033[33m{token}\033[0m")
            token_number += 1
            continue
        
        try:
            top_stack = STACK[-1]
        except IndexError:
            top_stack = None
            
        if top_stack and top_stack["end"] == token_number:
            if top_stack["type"] == "REPEAT":
                top_stack["times"] -= 1
                if top_stack["times"] > 0:
                    token_number = top_stack["start"]
                else:
                    STACK.pop()
                    next_non_ignore()
            if top_stack["type"] == "WHILE":
                condition = evaluate_tokens(top_stack["condition_tokens"])
                if condition["content"]:
                    token_number = top_stack["start"]
                else:
                    STACK.pop()
                    next_non_ignore()
            continue

        if token["class"] == "FUNCTION":
            function_name = token["subclass"]
            next_non_ignore()

            if not check_token_type(tokens[token_number], "DELIMITER", "LPAREN"):
                raise CodeError(
                    f"Expected '(' after {function_name.lower()}", error_code=1002
                )

            l_paren_token, parameters, num_parameters, r_paren_token = (
                get_function_tokens()
            )
            num_expected_parameters = EXPECTED_PARAMETERS[function_name]

            if num_parameters == num_expected_parameters:
                # Code for each function
                if function_name == "OUTPUT":
                    safe_execute(output, parameters)
            else:
                if num_parameters == 0:
                    error_token = l_paren_token
                else:
                    error_token = parameters[num_expected_parameters][0]

                raise CodeError(
                    f"Expected exactly {num_expected_parameters} parameter{plural_s(num_expected_parameters)} for output(), not {num_parameters}",
                    error_code=2001,
                    error_token=l_paren_token,
                )
            next_non_ignore()
            if token_number >= num_tokens or not check_token_type(
                tokens[token_number], "DELIMITER", "SEMICOLON"
            ):
                raise CodeError(
                    "Expected ';' at the end",
                    error_code=1001,
                    error_token=r_paren_token,
                )

        elif token["class"] == "KEYWORD":
            keyword_name = token["subclass"]
            next_non_ignore()
            keyword_tokens = get_keyword_tokens()

            if keyword_name == "SET":
                safe_execute(kwd_set, keyword_tokens)
        elif token["class"] == "LOOP":
            loop_name = token["subclass"]
            next_non_ignore()
            if not check_token_type(tokens[token_number], "DELIMITER", "LPAREN"):
                raise CodeError(
                    f"Expected '(' after {loop_name.lower()}", error_code=1002
                )
            next_non_ignore()
            loop_parameters = []
            current_parameter = []
            while not check_token_type(tokens[token_number], "DELIMITER", "RPAREN"):
                if check_token_type(tokens[token_number], "DELIMITER", "COMMA"):
                    loop_parameters.append(current_parameter)
                    current_parameter = []

                current_parameter.append(tokens[token_number])
                next_non_ignore()
            if current_parameter:
                loop_parameters.append(current_parameter)
            next_non_ignore()
            if not check_token_type(tokens[token_number], "DELIMITER", "LBRACE"):
                raise CodeError(
                    "Expected '{' " + f"after {loop_name.lower()}", error_code=1009
                )
            next_non_ignore()
            loop_code = []
            loop_code_start = token_number
            while not check_token_type(tokens[token_number], "DELIMITER", "RBRACE"):
                loop_code.append(tokens[token_number])
                next_non_ignore()

                if token_number >= num_tokens:
                    raise CodeError(
                        "Expected '}' at the end",
                        error_code=1008,
                        error_token=loop_code[-1],
                    )
            loop_code_end = token_number

            if loop_name == "REPEAT":
                STACK.append(
                    {
                        "type": loop_name,
                        "times": evaluate_tokens(loop_parameters[0])["content"],
                        "start": loop_code_start,
                        "start_token": loop_code[0],
                        "end": loop_code_end,
                        "end_token": loop_code[-1],
                    }
                )
                
                token_number = loop_code_start - 1
            elif loop_name == "WHILE":
                condition_tokens = loop_parameters[0]
                if evaluate_tokens(condition_tokens)["content"]:
                    STACK.append(
                        {
                            "type": loop_name,
                            "condition_tokens": condition_tokens,
                            "start": loop_code_start,
                            "start_token": loop_code[0],
                            "end": loop_code_end,
                            "end_token": loop_code[-1],
                        }
                    )
                    
                    token_number = loop_code_start - 1
        else:
            raise CodeError(
                f"Unexpected token '{token['content']}'",
                error_code=1005,
                error_token=token,
            )

        next_non_ignore()
except CodeError as e:
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

end_time = default_timer()
if DEBUG_SHOW_TIME_TAKEN:
    print("\033[33mDEBUG Finished in", end_time - start_time, "seconds\033[0m")

if DEBUG_SHOW_VARIABLES_AT_END:
    print("\033[33mDEBUG", VARIABLES, "\033[0m")
