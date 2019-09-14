import ast

def get_assignment_name(code: str):
    first_item = ast.parse(code.strip()).body[0]
    if isinstance(first_item, ast.Assign):
        assignment = first_item.targets[0]
        if isinstance(assignment, ast.Name):
            return assignment.id
    raise Exception(f"the calling method is unexpected {code}")
