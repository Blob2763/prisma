from helper import *
from tokens import *
from error import CodeError

def func_output(parameters):
    to_print = parameters[0]
    evaluated = evaluate_tokens(to_print)
    stringify_content(evaluated)
    content = evaluated["content"]
    remove_quotes(content)
    
    print(content)
    
def kwd_set(keyword_tokens):
    if not check_token_type(keyword_tokens[0], "IDENTIFIER", "VARIABLE"):
        raise CodeError("Expected variable name after 'set'", error_code=1004, error_token=keyword_tokens[0])

    if not check_token_type(keyword_tokens[1], "OPERATION", "EQUALS"):
        raise CodeError("Expected '=' after variable name", error_code=1004, error_token=keyword_tokens[1])

    variable_token = keyword_tokens[0]
    variable_name = variable_token["content"]
    expression_tokens = keyword_tokens[2:]
    value = evaluate_tokens(expression_tokens)

    VARIABLES[variable_name] = value