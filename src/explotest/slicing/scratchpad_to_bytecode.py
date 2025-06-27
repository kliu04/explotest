import dis


with open("/Users/wevie/Documents/explotest/src/explotest/slicing/scratchpad.py") as f:
    print(dis.dis(f.read()))
