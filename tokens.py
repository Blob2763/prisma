from lex import tokenise
import re
from helper import plural_s

NUM_EXPECTED_PARAMETERS = {
    "OUTPUT": 1,
    "REPEAT": 1,
    "WHILE": 1,
}
MIN_KWD_TOKENS = {"SET": 3}

CODE_FILE = "code.prsm"

tokens = tokenise("rules.lexif", CODE_FILE)
with open(CODE_FILE, "r") as file:
    code = file.read()
    lines = code.split("\n")
    line_start_positions = [0] + [m.end() for m in re.finditer("\n", code)]

num_tokens = len(tokens)
token_number = 0
current_token = tokens[token_number]


def get_token_number():
    return token_number


def set_token_number(value):
    global token_number
    global current_token
    token_number = value
    try:
        current_token = tokens[token_number]
    except Exception as e:
        pass


def increment_token_number():
    set_token_number(get_token_number() + 1)


def get_current_token():
    return current_token


def get_line_start_positions():
    return line_start_positions


def get_lines():
    return lines


def skip_to_non_ignore():
    while token_number < num_tokens and tokens[token_number]["class"] == "IGNORE":
        increment_token_number()


def next_non_ignore():
    increment_token_number()
    if token_number < num_tokens:
        skip_to_non_ignore()


def find_line_number(position):
    return len(
        [
            line_start_pos
            for line_start_pos in line_start_positions
            if line_start_pos <= position
        ]
    )


def check_token_type(token, token_class, token_subclass):
    return token["class"] == token_class and token["subclass"] == token_subclass


def format_content(token):
    content = str(token["content"])

    if check_token_type(token, "LITERAL", "STRING"):
        token["content"] = content
    elif check_token_type(token, "LITERAL", "NUMBER"):
        try:
            token["content"] = int(content)
        except ValueError:
            token["content"] = float(content)
    elif check_token_type(token, "LITERAL", "BOOLEAN"):
        if content == "true":
            token["content"] == True
        if content == "false":
            token["content"] == False


def stringify_content(token):
    content = token["content"]

    if check_token_type(token, "LITERAL", "STRING"):
        token["content"] = str(content)
    elif check_token_type(token, "LITERAL", "NUMBER"):
        token["content"] = str(content)
    elif check_token_type(token, "LITERAL", "BOOLEAN"):
        if content == True:
            token["content"] = "true"
        if content == False:
            token["content"] = "false"


from error import CodeError


def get_parameters(name):
    parameters = []
    current_parameter = []
    while not check_token_type(get_current_token(), "DELIMITER", "RPAREN"):
        if check_token_type(get_current_token(), "DELIMITER", "COMMA"):
            parameters.append(current_parameter)
            current_parameter = []
        else:
            current_parameter.append(get_current_token())
        next_non_ignore()

        if get_token_number() >= num_tokens:
            raise CodeError(
                "Expected ')' at the end",
                error_code=1006,
                error_token=current_parameter[-1],
            )

    if current_parameter:
        parameters.append(current_parameter)

    num_parameters = len(parameters)

    num_expected_parameters = NUM_EXPECTED_PARAMETERS[name]
    if num_parameters != num_expected_parameters:
        if num_parameters == 0:
            error_token = None
        else:
            error_token = parameters[num_expected_parameters][0]

        raise CodeError(
            f"Expected exactly {num_expected_parameters} parameter{plural_s(num_expected_parameters)} for {name.lower()}, not {num_parameters}",
            error_code=2001,
            error_token=error_token,
        )

    return parameters, num_parameters


def get_function_tokens(function_name):
    l_paren_token = get_current_token()
    next_non_ignore()
    parameters, num_parameters = get_parameters(function_name)
    r_paren_token = get_current_token()

    return l_paren_token, parameters, num_parameters, r_paren_token


def get_keyword_tokens(keyword_name):
    keyword_tokens = []
    while not check_token_type(get_current_token(), "DELIMITER", "SEMICOLON"):
        current_token = get_current_token()

        keyword_tokens.append(current_token)
        if (
            get_token_number() >= num_tokens
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

    min_keyword_tokens = MIN_KWD_TOKENS[keyword_name]
    if len(keyword_tokens) < min_keyword_tokens:
        raise CodeError("Unfinished statement", error_code=1009)

    return keyword_tokens


def get_loop_tokens(loop_name):
    if not check_token_type(get_current_token(), "DELIMITER", "LPAREN"):
        raise CodeError(f"Expected '(' after {loop_name.lower()}", error_code=1002)
    next_non_ignore()

    loop_parameters, num_parameters = get_parameters(loop_name)
    next_non_ignore()

    if not check_token_type(get_current_token(), "DELIMITER", "LBRACE"):
        raise CodeError("Expected '{' " + f"after {loop_name.lower()}", error_code=1009)
    next_non_ignore()

    loop_code = []
    loop_code_start = get_token_number()
    while not check_token_type(get_current_token(), "DELIMITER", "RBRACE"):
        loop_code.append(get_current_token())
        next_non_ignore()

        if get_token_number() >= num_tokens:
            raise CodeError(
                "Expected '}' at the end",
                error_code=1008,
                error_token=loop_code[-1],
            )
    loop_code_end = get_token_number()

    return loop_parameters, loop_code_start, loop_code, loop_code_end
