from ast import *
from typing import Any

from src.explotest.pytest_fixture import PyTestFixture
from src.explotest.reconstructor import Reconstructor


def _make_ptf_empty(deps: list[PyTestFixture], param: str):
    ptf = PyTestFixture(deps, param, [Pass()], Return(value=Constant(value=None)))
    return ptf

def test_reconstructor_fixture_bfs():
    n4 = _make_ptf_empty([], 'n4')
    n3 = _make_ptf_empty([], 'n3')
    n2 = _make_ptf_empty([], 'n2')
    n1 = _make_ptf_empty([], 'n1')
    n5 = _make_ptf_empty([], 'n5')
    n1.depends = [n2]
    n2.depends = [n3]
    n3.depends = [n4, n5]
    n5.depends = [n1]
    n4.depends = [n2]

    assert {n1, n2, n3, n4, n5} == set(Reconstructor.fixture_bfs(n1))

class ReconstructorInheritor(Reconstructor):

    def _ast(self, parameter: str, argument: Any) -> PyTestFixture:
        return _make_ptf_empty(argument, parameter)


def test_ast_walks_all_fixtures():
    r = ReconstructorInheritor('')
    result = r.asts({
        'x': [_make_ptf_empty([], '1')],
        'y': [],
        'z': []
    })

    assert {'x', 'y', 'z', '1'} == set([v.parameter for v in result])