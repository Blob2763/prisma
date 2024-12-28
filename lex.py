# Docs at https://github.com/Blob2763/lex

import re


def extract_quote_strings(string: str) -> list:
    """
    Extracts all substrings surrounded by a pair of quotes. Quotes can be
    single (') or double ("), but each pair of quotes must consist of two of
    the same quotes.

    For example, `extract_quote_strings('Hello, "world"!')` -> `["world"]`

    Parameters:
        string (str): the main string

    Returns:
        substrings_found (list): a list of all the substrings found, the
        original quotes are not in the string
    """

    strings_found = []
    current_token = ""
    inside_quotes = False
    quote_char = ""  # To track which quote type we're inside (' or ")

    for char in string:
        if not inside_quotes:
            # Check if we find an opening quote
            if char == '"' or char == "'":
                inside_quotes = True
                quote_char = char  # Remember the type of quote
                current_token = char  # Start the token with the opening quote
        else:
            # We're inside quotes
            current_token += char
            if char == quote_char:
                # If it's the closing quote, save the token
                strings_found.append(
                    current_token.strip(quote_char).encode().decode("unicode_escape")
                )
                current_token = ""
                inside_quotes = False
                quote_char = ""

    return strings_found


def is_following_rule(string: str, rule: dict) -> bool:
    """
    Checks whether a certain string is following a rule.

    Parameters:
        string (str): the string to test
        rule (dict): the rule to test against

    Returns:
        is_pass (bool): whether or not the string follows the rule
    """

    match rule["rule_type"]:
        case "equal":
            return string == rule["check_string"]
        case "between":
            return (
                string.startswith(rule["start_string"])
                and string.endswith(rule["end_string"])
                and len(string) >= 2
            )
        case "regex":
            return re.fullmatch(rule["pattern"], string)
        case "endswith":
            return string.endswith(rule["end_string"])
        

def is_following_group(group: dict, token: dict, next_token: dict) -> bool:
    """
    Checks whether a certain pair of tokens should be grouped.

    Parameters:
        group (dict): the group to test
        token (dict): the first token
        next_token (dict): the second token

    Returns:
        is_pass (bool): whether or not the tokens should be grouped
    """
    
    return (
        group["parts"][0]["class"] == token["class"]
        and group["parts"][0]["subclass"] == token["subclass"]
        and group["parts"][1]["class"] == next_token["class"]
        and group["parts"][0]["subclass"] == token["subclass"]
    )


def split_rule_string(rule_string: str):
    """
    Splits a rule string into separate parts.

    Parameters:
        rule_string (str): the rule string to be split

    Returns:
        match_part (str): all the text after the arrow
        class_name (str): the name of the class of the rule
        subclass_name (str): the name of the subclass of the rule
        match_type (str): the type of match defined by the arrow
    """

    arrow = rule_string.split(maxsplit=3)[-2]
    (type_part, match_part) = rule_string.split(arrow)
    type_part = type_part.strip()
    match_part = match_part.strip()
    (class_name, subclass_name) = type_part.split(" ")
    match arrow:
        case "->":
            match_type = "normal"
        case "=>":
            match_type = "greedy"

    return match_part, class_name, subclass_name, match_type


def generate_rules(rules_file):
    """
    Generates a list of rules based on the contents of a rules file.

    Parameters:
        rules_file (str): the rules in the rules file

    Returns:
        rules (list): a list of all the rules as dictionaries
        groups (list): a list of all the rules for groups as dictionaries
    """

    all_lines = [rule for rule in rules_file.split("\n") if rule.strip() != ""]

    constant_strings = []
    rule_strings = []
    group_strings = []
    current_header = ""
    for line in all_lines:
        if line.startswith("#"):
            # found a header
            current_header = line
            continue

        match current_header:
            case "#CONSTANTS":
                constant_strings.append(line)
            case "#RULES":
                rule_strings.append(line)
            case "#GROUPS":
                group_strings.append(line)

    constants = []
    for constant_string in constant_strings:
        if constant_string.strip() == "":
            continue

        (name, replace) = constant_string.split(" -> ", maxsplit=1)
        constants.append(
            {"name": name, "replace": replace.encode().decode("unicode_escape")}
        )

    rules = []
    for rule_string in rule_strings:
        for constant in constants:
            rule_string = rule_string.replace(constant["name"], constant["replace"])

        (match_part, class_name, subclass_name, match_type) = split_rule_string(
            rule_string
        )

        rule = {
            "class": class_name,
            "subclass": subclass_name,
            "match_type": match_type,
        }

        # equal
        if match_part.startswith("is"):
            rule["rule_type"] = "equal"
            rule["check_string"] = extract_quote_strings(match_part)[0]
            rules.append(rule)
            continue

        # between two certain strings
        if match_part.startswith("between"):
            rule["rule_type"] = "between"

            end_strings = extract_quote_strings(match_part)

            rule["start_string"] = end_strings[0]
            rule["end_string"] = end_strings[1]
            rules.append(rule)
            continue

        # check for regex
        if match_part.startswith("matches"):
            rule["rule_type"] = "regex"
            rule["pattern"] = (
                match_part.strip("matches").strip().encode().decode("unicode_escape")
            )
            rules.append(rule)
            continue

        # check if ends with string
        if match_part.startswith("endswith"):
            rule["rule_type"] = "endswith"
            rule["end_string"] = extract_quote_strings(match_part)[0]
            rules.append(rule)
            continue

    groups = []
    for group_string in group_strings:
        result, parts_string = group_string.split(" -> ")
        result_class, result_subclass = result.split(" ")
        parts_full = parts_string.split(" + ")
        parts = []
        for part_string in parts_full:
            part_class, part_subclass = part_string.split(" ")
            parts.append({"class": part_class, "subclass": part_subclass})
        group_data = {
            "result_class": result_class,
            "result_subclass": result_subclass,
            "parts": parts,
        }

        groups.append(group_data)

    return rules, groups


def tokenise(rules_path: str, code_path: str) -> list:
    """
    Splits the code into a list of tokens.

    Parameters:
        rules_path (str): the path to the rules file (must be a .lexif file)
        code_path (str): the path to the code to be tokenised

    Returns:
        tokens (list): a list of all the token dictionaries
    """

    if not rules_path.endswith(".lexif"):
        raise ValueError("rules file should be a .lexif file")

    rules_file = open(rules_path, "r", encoding="utf-8").read()
    rules, groups = generate_rules(rules_file)

    code = open(code_path, "r", encoding="utf-8").read()

    line_start_positions = [0] + [m.end() for m in re.finditer("\n", code)]

    tokens = []
    current_token = ""
    recent_token_end = -1
    line_number = 1
    for i, char in enumerate(code):
        line_number = len(
            [
                line_start_position
                for line_start_position in line_start_positions
                if line_start_position <= i
            ]
        )

        current_token += char

        for rule in rules:
            is_normal_pass = rule["match_type"] == "normal" and is_following_rule(
                current_token, rule
            )
            if i < len(code) - 1:
                is_greedy_pass = (
                    rule["match_type"] == "greedy"
                    and is_following_rule(current_token, rule)
                    and not is_following_rule(current_token + code[i + 1], rule)
                )
            else:
                is_greedy_pass = rule["match_type"] == "greedy" and is_following_rule(
                    current_token, rule
                )

            if is_normal_pass or is_greedy_pass:
                tokens.append(
                    {
                        "class": rule["class"],
                        "subclass": rule["subclass"],
                        "content": current_token,
                        "start_position": recent_token_end + 1,
                        "end_position": i,
                        "line_number": line_number,
                    }
                )
                recent_token_end = i
                current_token = ""
                break
    if current_token != "":
        tokens.append(
            {
                "class": "ERROR",
                "subclass": "UNFINISHED_TOKEN",
                "content": current_token,
                "start_position": recent_token_end + 1,
                "end_position": i,
                "line_number": line_number,
            }
        )

    while True:
        has_grouped = False
        grouped_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                for group in groups:
                    if is_following_group(group, token, next_token):
                        has_grouped = True
                        new_token = {
                            "class": group["result_class"],
                            "subclass": group["result_subclass"],
                            "content": token["content"] + next_token["content"],
                            "start_position": token["start_position"],
                            "end_position": next_token["end_position"],
                            "line_number": token["line_number"],
                        }
                        
                        token = new_token
                        i += 1
            grouped_tokens.append(token)
            i += 1
        tokens = grouped_tokens
        
        if not has_grouped:
            # Break if no more groups can be made
            break

    return tokens
