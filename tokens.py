from lex import tokenise
import re

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
    # print("a", current_token)
    token_number = value
    try:
        current_token = tokens[token_number]
    except Exception as e:
        pass
    # print("b", current_token)


def increment_token_number():
    set_token_number(get_token_number() + 1)
    

def get_current_token():
    return current_token


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
    content = token["content"]

    if check_token_type(token, "LITERAL", "STRING"):
        token["content"] = str(content)
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