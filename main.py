from functions import *
from helper import *
from debug import *
from timeit import default_timer
from error import *
from tokens import *

start_time = default_timer()


def get_parameters():
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

    return parameters, num_parameters


def get_function_tokens():
    l_paren_token = get_current_token()
    next_non_ignore()
    parameters, num_parameters = get_parameters()
    r_paren_token = get_current_token()

    return l_paren_token, parameters, num_parameters, r_paren_token


def get_keyword_tokens():
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

    return keyword_tokens


def raise_code_error(error):
    raise CodeError(
        error,
        error_code=error.error_code,
        error_token=error.error_token,
    )


def safe_execute(func, parameters):
    try:
        return func(parameters)
    except CodeError as e:
        raise_code_error(e)


try:
    if check_token_type(tokens[-1], "ERROR", "UNFINISHED_TOKEN"):
        raise CodeError("Unfinished token", error_code=1003, error_token=tokens[-1])

    skip_to_non_ignore()
    while get_token_number() < num_tokens:
        token = get_current_token()
        
        if DEBUG_ONLY_TOKENS:
            print(f"\033[33m{token}\033[0m")
            token_number += 1
            continue
        
        try:
            top_stack = STACK[-1]
        except IndexError:
            top_stack = None
            
        if top_stack and top_stack["end"] == get_token_number():
            if top_stack["type"] == "REPEAT":
                top_stack["times"] -= 1
                if top_stack["times"] > 0:
                    set_token_number(top_stack["start"])
                else:
                    STACK.pop()
                    next_non_ignore()
            if top_stack["type"] == "WHILE":
                condition = evaluate_tokens(top_stack["condition_tokens"])
                if condition["content"]:
                    set_token_number(top_stack["start"])
                else:
                    STACK.pop()
                    next_non_ignore()
            continue

        if token["class"] == "FUNCTION":
            function_name = token["subclass"]
            next_non_ignore()

            if not check_token_type(get_current_token(), "DELIMITER", "LPAREN"):
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
            if get_token_number() >= num_tokens or not check_token_type(
                get_current_token(), "DELIMITER", "SEMICOLON"
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
            if not check_token_type(get_current_token(), "DELIMITER", "LPAREN"):
                raise CodeError(
                    f"Expected '(' after {loop_name.lower()}", error_code=1002
                )
            next_non_ignore()
            loop_parameters = []
            current_parameter = []
            while not check_token_type(get_current_token(), "DELIMITER", "RPAREN"):
                if check_token_type(get_current_token(), "DELIMITER", "COMMA"):
                    loop_parameters.append(current_parameter)
                    current_parameter = []

                current_parameter.append(get_current_token())
                next_non_ignore()
            if current_parameter:
                loop_parameters.append(current_parameter)
            next_non_ignore()
            if not check_token_type(get_current_token(), "DELIMITER", "LBRACE"):
                raise CodeError(
                    "Expected '{' " + f"after {loop_name.lower()}", error_code=1009
                )
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
                
                set_token_number(loop_code_start - 1)
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
                    
                    set_token_number(loop_code_start - 1)
        else:
            raise CodeError(
                f"Unexpected token '{token['content']}'",
                error_code=1005,
                error_token=token,
            )

        next_non_ignore()
except CodeError as e:
    display_error(e)

end_time = default_timer()
if DEBUG_SHOW_TIME_TAKEN:
    print("\033[33mDEBUG Finished in", end_time - start_time, "seconds\033[0m")

if DEBUG_SHOW_VARIABLES_AT_END:
    print("\033[33mDEBUG", VARIABLES, "\033[0m")
