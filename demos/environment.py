# Env is Symbol (Symbol -> Number) -> Number
# interp.  A collection of deferred substitutions
from explotest import explore


# -> Env
@explore(mode="p")
def empty_env():
    return lambda x, fail: fail(x)

# Env Symbol Number -> Env
@explore(mode="p")
def extend_env(env, x0: str, v: int):
    return lambda x, fail: v if x == x0 else env(x, fail)

# Env Symbol -> Number
@explore(mode="p")
def lookup_env(env, x):
    def raise_unbound(var):
        raise Exception(f"Unbound variable {var}")
    return env(x, lambda var: raise_unbound(var))

# Env Env -> Env
@explore(mode="p")
def combine_env(e0, e1):
    return lambda x, fail: e0(x, lambda x2: e1(x2, fail))

env0 = empty_env()
env1 = extend_env(env0, "x", 10)
env2 = extend_env(env1, "y", 20)

lookup = lookup_env(env2, "y")
print(lookup)

try:
    lookup_env(env2, "z")
except Exception as e:
    print(e)

env3 = extend_env(env0, "z", 30)
env4 = extend_env(env0, "g", 40)

env5 = combine_env(env2, env4)
lookup = lookup_env(env5, "x")
print(lookup)
