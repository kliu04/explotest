import explotest


@explotest.explore_slice
def describe_match(key, actual, expected):
    return f"The key '{key}' was expected to be '{expected}' and it was actually '{actual}': Match = {actual == expected}"


name = "Alice"
age = 30
height = 5.5
is_student = False
profile = {"name": name, "age": age, "height": height, "is_student": is_student}
expected_profile = {"name": "Alice", "age": 30, "height": 5.5, "is_student": False}
actual_age = profile.get("age")
expected_age = expected_profile["age"]
msg2 = describe_match("age", actual_age, expected_age)
