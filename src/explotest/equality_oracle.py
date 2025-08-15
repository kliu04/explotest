import sys

from explotest.oracle import Oracle


class EqualityOracle(Oracle):
    def run(self, node, collected_args):
        try:
            sys.call_tracing(lambda: exec(compile(node, "", "exec"), {}), ())
        except:
            return False
        return 1 in []
