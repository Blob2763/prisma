from copy import deepcopy

VARIABLES = {}
STACK = []


class FakeCodeError(Exception):
    def __init__(self, message, error_code, error_token=None):
        super().__init__(message)
        self.error_code = error_code
        self.error_token = error_token


def check_token_type(token, token_class, token_subclass):
    return token["class"] == token_class and token["subclass"] == token_subclass


def infix_to_postfix(tokens):
    precedence = {
        "PLUS": 1,
        "MINUS": 1,
        "TIMES": 2,
        "DIVIDE": 2,
        "MODULO": 2,
        "POWER": 3,
        "LESS_THAN": 0,
        "GREATER_THAN": 0,
        "LESS_EQUAL": 0,
        "GREATER_EQUAL": 0,
        "EQUAL": 0,
        "NOT_EQUAL": 0,
        "AND": -1,
        "OR": -2
    }

    stack = []
    postfix = []

    for token in tokens:
        if check_token_type(token, "IDENTIFIER", "VARIABLE"):
            try:
                token = VARIABLES[token["content"]]
            except KeyError:
                raise FakeCodeError(
                    f"Undefined variable: {token['content']}",
                    error_code=2002,
                    error_token=token,
                )

        if check_token_type(token, "LITERAL", "NUMBER"):
            postfix.append(token)
        elif token["class"] == "OPERATION":
            while (
                stack
                and stack[-1]["class"] == "OPERATION"
                and precedence[stack[-1]["subclass"]] >= precedence[token["subclass"]]
            ):
                postfix.append(stack.pop())
            stack.append(token)
        elif check_token_type(token, "DELIMITER", "LPAREN"):
            stack.append(token)
        elif check_token_type(token, "DELIMITER", "RPAREN"):
            while stack and not check_token_type(stack[-1], "DELIMITER", "LPAREN"):
                postfix.append(stack.pop())
            if not stack:
                raise FakeCodeError(
                    "Mismatched parentheses: Missing left parenthesis.",
                    error_code=1005,
                    error_token=token,
                )
            stack.pop()
        else:
            # Unexpected token
            if check_token_type(token, "LITERAL", "STRING"):
                raise FakeCodeError(
                    "Cannot perform arithmetic on STRING",
                    error_code=2003,
                    error_token=token,
                )

            raise ValueError(f"Unexpected token: {token}")

    # Pop any remaining operators in the stack
    while stack:
        if check_token_type(stack[-1], "DELIMITER", "LPAREN"):
            raise FakeCodeError(
                "Mismatched parentheses: Missing right parenthesis.",
                error_code=1005,
                error_token=stack[-1],
            )
        postfix.append(stack.pop())

    return postfix


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


def evaluate_postfix(tokens):
    stack = []

    for token in tokens:
        if check_token_type(token, "LITERAL", "NUMBER"):
            stack.append(token)
        elif token["class"] == "OPERATION":
            b = stack.pop()
            format_content(b)
            b = b["content"]
            
            a = stack.pop()
            format_content(a)
            a = a["content"]

            if token["subclass"] == "PLUS":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a + b,
                    }
                )
            elif token["subclass"] == "MINUS":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a - b,
                    }
                )
            elif token["subclass"] == "TIMES":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a * b,
                    }
                )
            elif token["subclass"] == "DIVIDE":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a / b,
                    }
                )
            elif token["subclass"] == "MODULO":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a % b,
                    }
                )
            elif token["subclass"] == "POWER":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "NUMBER",
                        "content": a ** b,
                    }
                )

            elif token["subclass"] == "LESS_THAN":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a < b,
                    }
                )
            elif token["subclass"] == "GREATER_THAN":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a > b,
                    }
                )
            elif token["subclass"] == "EQUAL_TO":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a == b,
                    }
                )
            elif token["subclass"] == "LESS_EQUAL":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a <= b,
                    }
                )
            elif token["subclass"] == "GREATER_EQUAL":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a >= b,
                    }
                )
            elif token["subclass"] == "NOT_EQUAL":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a != b,
                    }
                )
            elif token["subclass"] == "AND":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a and b,
                    }
                )
            elif token["subclass"] == "OR":
                stack.append(
                    {
                        "class": "LITERAL",
                        "subclass": "BOOLEAN",
                        "content": a or b,
                    }
                )

    format_content(stack[0])
    return stack[0]


def evaluate_tokens(tokens):
    tokens = deepcopy(tokens)  # Avoid original tokens being altered
    
    if len(tokens) == 0:
        raise FakeCodeError("Expected expression", 1006)

    # Replace variables with their values
    for i, token in enumerate(tokens):
        if check_token_type(token, "IDENTIFIER", "VARIABLE"):
            try:
                tokens[i] = VARIABLES[token["content"]]
                tokens[i]["start_position"] = token["start_position"]
                tokens[i]["end_position"] = token["end_position"]
                tokens[i]["line_number"] = token["line_number"]
            except KeyError as e:
                raise FakeCodeError(
                    f"Variable {e} is not defined", error_code=2002, error_token=token
                )

    if len(tokens) == 1 and check_token_type(tokens[0], "LITERAL", "STRING"):
        return tokens[0]
    else:
        return evaluate_postfix(infix_to_postfix(tokens))


def insert_substrings(original_string, substring1, position1, substring2, position2):
    return (
        original_string[:position1]
        + substring1
        + original_string[position1:position2]
        + substring2
        + original_string[position2:]
    )


def plural_s(num):
    return "s" if num != 1 else ""