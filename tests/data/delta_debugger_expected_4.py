import explotest


@explotest.explore("s")
def describe_match(key, actual, expected):
    return f"The key '{key}' was expected to be '{expected}' and it was actually '{actual}': Match = {actual == expected}"


name = "Alice"
age = 30
height = 5.5
is_student = False
profile = {"name": name, "age": age, "height": height, "is_student": is_student}
expected_profile = {"name": "Alice", "age": 30, "height": 5.5, "is_student": False}
actual_student_status = profile["is_student"]
expected_student_status = expected_profile["is_student"]
msg4 = describe_match("is_student", actual_student_status, expected_student_status)
