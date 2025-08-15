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
actual_name = profile["name"]
expected_name = expected_profile["name"]
msg1 = describe_match("name", actual_name, expected_name)
