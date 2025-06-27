import ast

with open("/Users/wevie/Documents/explotest/src/explotest/slicing/scratchpad.py") as f:
    print(ast.dump(ast.parse(f.read()), indent=4, include_attributes=False))
