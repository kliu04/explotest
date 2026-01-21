import argparse
import ast
import shlex
from typing import override

from IPython.core.error import UsageError
from IPython.core.magic import magics_class, Magics, line_magic, needs_local_scope
from IPython.lib.pretty import pretty


class ExplotestArgumentParser(argparse.ArgumentParser):
    @override
    def error(self, message):
        raise UsageError(f"prog: {self.prog}, {message}")


parser = ExplotestArgumentParser(
    prog="explotest",
    description="ExploTest, a unit test generation tool.",
    epilog="For help, contact randy <at> randyzhu.com.",
)

parser.add_argument("function_call", type=str)


@magics_class
class ExplotestMagics(Magics):
    @line_magic
    @needs_local_scope
    def explore(self, line: str, local_ns: dict[str, object]):
        args: argparse.Namespace = parser.parse_args(shlex.split(line))
        assert args.function_call is not None
        assert isinstance(args.function_call, str)

        function_name: str = args.function_call[: args.function_call.find("(")]

        # try to parse the function call to see if it's legit
        function_call_ast: ast.Expression = ast.parse(args.function_call, mode="eval")

        if function_name not in local_ns.keys():
            msg = f"{function_name} is not defined. Current definitions:\n"
            for key, val in local_ns.items():
                msg += f"{key}: {val}\n"
            raise ValueError(msg)

        # note: we don't actually *call* function_obj directly, instead, we evaluate whether it's really callable
        # before we evaluate it in the shell.
        function_obj = local_ns[function_name]

        if function_obj is None:
            raise ValueError(
                f"{function_obj} is None! Re-check your function definitions."
            )
        elif not callable(function_obj):
            raise ValueError(
                f"{function_obj} is not callable. It is instead of type: {type(function_obj)}"
            )

        # import explotest
        import explotest

        local_ns["explotest"] = explotest

        # First, get the wrapped function using explore
        explore_call = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="explotest"), attr="explore", ctx=ast.Load()
            ),
            args=[function_call_ast.body.func],
        )

        # Then call the wrapped function with the original arguments
        call_body: ast.Call = function_call_ast.body
        new_call_with_explore = ast.Call(
            func=explore_call,
            args=call_body.args,
            keywords=getattr(call_body, "keywords", []),
        )

        print(ast.dump(new_call_with_explore, indent=4))

        call_result = self.shell.ev(
            ast.unparse(ast.fix_missing_locations(new_call_with_explore))
        )

        print(f"Result: {pretty(call_result)}")
        # print(local_ns)
