from functions import *
from helper import *
from debug import *
from timeit import default_timer
from error import *
from tokens import *

start_time = default_timer()


try:
    if check_token_type(tokens[-1], "ERROR", "UNFINISHED_TOKEN") and not DEBUG_ONLY_TOKENS:
        raise CodeError("Unfinished token", error_code=1003, error_token=tokens[-1])

    skip_to_non_ignore()
    while get_token_number() < num_tokens:
        token = get_current_token()

        if DEBUG_ONLY_TOKENS:
            print(f"\033[33m{token}\033[0m")
            increment_token_number()
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
                get_function_tokens(function_name)
            )

            # Code for each function
            if function_name == "OUTPUT":
                func_output(parameters)

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
            keyword_tokens = get_keyword_tokens(keyword_name)

            if keyword_name == "SET":
                kwd_set(keyword_tokens)

        elif token["class"] == "LOOP":
            loop_name = token["subclass"]
            next_non_ignore()
            loop_parameters, loop_code_start, loop_code, loop_code_end = (
                get_loop_tokens(loop_name)
            )

            if loop_name == "REPEAT":
                if evaluate_tokens(loop_parameters[0])["content"] >= 1:
                    STACK.append(
                        {
                            "type": loop_name,
                            "times": int(evaluate_tokens(loop_parameters[0])["content"]),
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
