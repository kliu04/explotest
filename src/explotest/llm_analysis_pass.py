import ast

import openai
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


# from .explore import explore

class LLMAnalyzer:
    llm: openai.OpenAI
    fn_def: ast.FunctionDef
    globals: dict[str, object]
    model: str
    SYSTEM_PROMPT = """
    You are an expert senior Python QA developer with expertise in writing unit tests.
    
    An external variable is a reference to a variable outside of the function.
    External variables should be mocked if the function will not work without them, or if they are modified.
    Some types of external variables are functions, and are called with parenthesis. Use the docstring of the variable
    or package to determine whether they affect external state, like network calls, database operations, or file I/O.
    You can also use the name of the variable to infer whether it should be mocked. 
      
    You are given:
        - a docstring of a variable external to the function, which starts with <docstring> and ends with </docstring>.
        This describes what the variable is
        - the source code of the function, starting with <source>, ending with </source>. This source is your function of
        interest.
        - the name of the external variable, starting with <name> and ending with </name>.
        
    Example 1:
    <docstring>
    Built-in mutable sequence.\n\nIf no argument is given, the constructor creates a new empty list.\nThe argument must be an iterable if specified.
    </docstring>
    
    <source>
    def foo():
        x = 3
        L.append(x)
    </source>
    
    <name>
    L
    </name>
    
    Response: yes
    
    Example 2:
    <docstring>
    \nNumPy\n=====\n\nProvides\n  1. An array object of arbitrary homogeneous items\n  2. Fast mathematical operations over arrays\n  3. Linear Algebra, Fourier Transforms, Random Number Generation\n\nHow to use the documentation\n----------------------------\nDocumentation is available in two forms: docstrings provided\nwith the code, and a loose standing reference guide, available from\n`the NumPy homepage <https://numpy.org>`_.\n\nWe recommend exploring the docstrings using\n`IPython <https://ipython.org>`_, an advanced Python shell with\nTAB-completion and introspection capabilities.  See below for further\ninstructions.\n\nThe docstring examples assume that `numpy` has been imported as ``np``::\n\n  >>> import numpy as np\n\nCode snippets are indicated by three greater-than signs::\n\n  >>> x = 42\n  >>> x = x + 1\n\nUse the built-in ``help`` function to view a function\'s docstring::\n\n  >>> help(np.sort)\n  ... # doctest: +SKIP\n\nFor some objects, ``np.info(obj)`` may provide additional help.  This is\nparticularly true if you see the line "Help on ufunc object:" at the top\nof the help() page.  Ufuncs are implemented in C, not Python, for speed.\nThe native Python help() does not know how to view their help, but our\nnp.info() function does.\n\nAvailable subpackages\n---------------------\nlib\n    Basic functions used by several sub-packages.\nrandom\n    Core Random Tools\nlinalg\n    Core Linear Algebra Tools\nfft\n    Core FFT routines\npolynomial\n    Polynomial tools\ntesting\n    NumPy testing tools\ndistutils\n    Enhancements to distutils with support for\n    Fortran compilers support and more (for Python <= 3.11)\n\nUtilities\n---------\ntest\n    Run numpy unittests\nshow_config\n    Show numpy build configuration\n__version__\n    NumPy version string\n\nViewing documentation using IPython\n-----------------------------------\n\nStart IPython and import `numpy` usually under the alias ``np``: `import\nnumpy as np`.  Then, directly past or use the ``%cpaste`` magic to paste\nexamples into the shell.  To see which functions are available in `numpy`,\ntype ``np.<TAB>`` (where ``<TAB>`` refers to the TAB key), or use\n``np.*cos*?<ENTER>`` (where ``<ENTER>`` refers to the ENTER key) to narrow\ndown the list.  To view the docstring for a function, use\n``np.cos?<ENTER>`` (to view the docstring) and ``np.cos??<ENTER>`` (to view\nthe source code).\n\nCopies vs. in-place operation\n-----------------------------\nMost of the functions in `numpy` return a copy of the array argument\n(e.g., `np.sort`).  In-place versions of these functions are often\navailable as array methods, i.e. ``x = np.array([1,2,3]); x.sort()``.\nExceptions to this rule are documented.\n\n
    </docstring>
    
    <source>
    import numpy as np

    def sigmoid(x):
      return 1 / (1 + np.exp(-x))
    </source>
    
    <name>
    np
    </name>
    
    Response: no
    """

    def __init__(
        self,
        llm: openai.OpenAI,
        fn_def: ast.FunctionDef,
        globals: dict[str, object],
        model: str,
    ):
        self.llm = llm
        self.fn_def = fn_def
        self.globals = globals
        self.model = model

    def filter_mocks(self) -> dict[str, object]:
        """
        Using the functiondef and globals, find out which globals need to be mocked
        """
        filtered: dict[str, object] = {}

        for name, obj in self.globals.items():
            prompt = f"""
<docstring>
{obj.__doc__}
</docstring>

<source>
{ast.unparse(ast.fix_missing_locations(self.fn_def))}
</source>

<name>
{name}
</name>
"""
            # print(f"Prompting... {prompt}")
            query = self.llm.chat.completions.create(
                model=self.model,
                reasoning_effort="medium",
                messages=[
                    ChatCompletionSystemMessageParam(
                        content=self.SYSTEM_PROMPT, role="system"
                    ),
                    ChatCompletionUserMessageParam(
                        content=prompt,
                        role="user",
                    ),
                ],
            )
            # print(f"Response: {query.choices[0].message.content}")
            if "yes" in query.choices[0].message.content.lower():
                filtered[name] = obj
            elif "no" in query.choices[0].message.content.lower():
                pass
            else:
                raise ValueError(f"LLM Output: {query.choices[0]}")

        return filtered
