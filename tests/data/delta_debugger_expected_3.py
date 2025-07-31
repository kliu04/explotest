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
actual_height = profile.get("height", None)
expected_height = expected_profile["height"]
msg3 = describe_match("height", actual_height, expected_height)
