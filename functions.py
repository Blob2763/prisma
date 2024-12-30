from helper import *
from tokens import *

EXPECTED_PARAMETERS = {"OUTPUT": 1}

def output(parameters):
    to_print = parameters[0]
    try:
        evaluated = evaluate_tokens(to_print)
    except FakeCodeError as e:
        raise FakeCodeError(e, error_code=e.error_code, error_token=e.error_token)
    
    evaluated = evaluate_tokens(to_print)
    stringify_content(evaluated)
    content = evaluated["content"]
    
    if content.startswith('"') and content.endswith('"'):
        content = content.strip('"')
    elif content.startswith("'") and content.endswith("'"):
        content = content.strip("'")
    
    print(content)
    
def kwd_set(keyword_tokens):
    if not check_token_type(keyword_tokens[0], "IDENTIFIER", "VARIABLE"):
        raise FakeCodeError("Expected variable name after SET", error_code=1004)

    variable_token = keyword_tokens[0]
    variable_name = variable_token["content"]
    expression_tokens = keyword_tokens[2:]

    VARIABLES[variable_name] = evaluate_tokens(expression_tokens)