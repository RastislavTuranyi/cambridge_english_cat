from pytest import fixture
from numpy import zeros

from tester import Tester, LowCertaintyError, InconsistentResultsError


parameters = zeros((50, 3), dtype=object)
parameters[0, 0] = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
parameters[0, 1] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 0/27
parameters[0, 2] = ('pre-A1', 1, 0, None, None, None)

parameters[1, 0] = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
parameters[1, 1] = [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]  # 7/27
parameters[1, 2] = ('pre-A1', 2, 0, None, None, None)

parameters[2, 0] = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
parameters[2, 1] = [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0]  # 13/27
parameters[2, 2] = ('pre-A1', 3, 0, None, None, None)

parameters[3, 0] = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
parameters[3, 1] = [0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1]  # 18/27
parameters[3, 2] = ('pre-A1', 4, 0, None, None, None)

parameters[4, 0] = [3, 2, 1, 0, 0] + [0, 0, 0, 0, 0, 1, 1, 1, 1, 1] * 2 + [0, 0, 0, 0, 0]
parameters[4, 1] = [0, 0, 0, 0, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 0, 0] * 2 + [1, 1, 1, 1, 1]  # 16/17 > 0.85
parameters[4, 2] = ('pre-A1', 5, 1, None, None, None)

parameters[5, 0] = [3, 2, 1, 0, 0] + [0, 0, 0, 0, 0, 1, 1, 1, 1, 1] * 2 + [0, 0, 0, 0, 0]
parameters[5, 1] = [0, 0, 0, 0, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 1, 1] * 2 + [1, 1, 1, 1, 1]  # 0.45 > 4/11 > 0.25
parameters[5, 2] = ('pre-A1', 5, 2, None, None, None)

parameters[6, 0] = [3, 2, 1, 0, 0] + [0, 0, 0, 0, 0] + [1, 1, 1, 1, 1] * 4
parameters[6, 1] = [0, 0, 0, 0, 1] + [1, 1, 1, 1, 1] + [0, 0, 1, 1, 1] * 4  # 0.65 > 12/21 > 0.45
parameters[6, 2] = ('pre-A1', 5, 3, None, None, None)

parameters[7, 0] = [3, 2, 1, 0, 0] + [0, 0, 0, 0, 0] + [1, 1, 1, 1, 1] * 4
parameters[7, 1] = [0, 0, 0, 0, 1] + [1, 1, 1, 1, 1] + [0, 1, 1, 1, 1] * 4  # 0.85 > 16/21 > 0.65
parameters[7, 2] = ('A1', 5, 4, None, None, None)

parameters[8, 0] = [3, 2, 1, 0, 0] + [0, 0, 0, 0, 0] + [1, 1, 1, 1, 1, 2, 2, 2, 2, 2] * 2
parameters[8, 1] = [0, 0, 0, 0, 1] + [1, 1, 1, 1, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 0, 0] * 2  # 16/21 > 0.85
parameters[8, 2] = ('A1', 5, 5, 'E', None, None)

parameters[9, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1, 2, 2, 2, 2, 2] * 2 + [1, 1, 1, 1, 1]
parameters[9, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 0, 0] * 2 + [1, 1, 1, 1, 1]  # 16/21 > 0.85
parameters[9, 2] = ('A1', 0, 5, 'E', None, None)

parameters[10, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1, 2, 2, 2, 2, 2] * 2 + [1, 1, 1, 1, 1]
parameters[10, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 0, 1] * 2 + [1, 1, 1, 1, 1]  # 2/12 < 13/30
parameters[10, 2] = ('A1', 0, 5, 'E', None, None)

parameters[11, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1, 2, 2, 2, 2, 2] * 2 + [1, 1, 1, 1, 1]
parameters[11, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1, 0, 0, 0, 1, 1] * 2 + [1, 1, 1, 1, 1]  # 4/12 < 13/30
parameters[11, 2] = ('A1', 0, 5, 'E', None, None)

parameters[12, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1] + [2, 2, 2, 2, 2] * 4
parameters[12, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1] + [0, 0, 1, 1, 1] * 4  # 2/3 > 12/22 > 13/30
parameters[12, 2] = ('A1', 0, 5, 'D', None, None)

parameters[13, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1] + [2, 2, 2, 2, 2, 3, 3, 3, 3, 3] * 2
parameters[13, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1] + [0, 1, 1, 1, 1, 0, 0, 1, 1, 1] * 2  # 0.886 > 8/12 > 2/3
parameters[13, 2] = ('A2', 0, 0, 'C', 'D', None)

parameters[14, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1] + [2, 2, 2, 2, 2, 3, 3, 3, 3, 3] * 2
parameters[14, 1] = [0, 0, 1, 1, 1] + [1, 1, 1, 1, 1] + [1, 1, 1, 1, 1, 0, 0, 1, 1, 1] * 2  # 28/30 > 10/12 > 0.886
parameters[14, 2] = ('A2', 0, 0, 'B', 'D', None)

parameters[15, 0] = [3, 2, 3, 2, 3] + [2, 2, 2, 2, 2, 3, 3, 3, 3, 3] * 2 + [4, 4, 4, 4, 4]
parameters[15, 1] = [0, 1, 0, 1, 0] + [1, 1, 1, 1, 1, 1, 1, 1, 1, 1] * 2 + [0, 0, 0, 1, 1]  # 17/17 > 28/30
parameters[15, 2] = ('B1', 0, 0, 'A', 'C', 'D')


@fixture(params=[i for i in [j for j, k in enumerate(parameters[:, 0]) if k]])
def initiate_tester(request):
    tester = Tester()
    tester.difficulties = parameters[request.param, 0]
    tester.scores = parameters[request.param, 1]
    tester.qtypes = ['' for __ in range(30)]
    tester.evaluate()
    return tester, parameters[request.param, 2]


def test_result_correct(initiate_tester):
    tester, expected_answer = initiate_tester
    assert tester.result == expected_answer[0]


def test_a0_shields_correct(initiate_tester):
    tester, expected_anser = initiate_tester
    assert tester.shields[0] == expected_anser[1]


def test_a1_shields_correct(initiate_tester):
    tester, expected_anser = initiate_tester
    assert tester.shields[1] == expected_anser[2]


def test_a2_grade(initiate_tester):
    tester, expected_anser = initiate_tester
    assert tester.grades[2] == expected_anser[3]


def test_b1_grade_correct(initiate_tester):
    tester, expected_anser = initiate_tester
    assert tester.grades[3] == expected_anser[4]


"""parameters[14, 0] = [3, 2, 1, 2, 1] + [1, 1, 1, 1, 1] + [2, 2, 2, 2, 2, 3, 3, 3, 3, 3] * 2
parameters[14, 1] = [0, 0, 1, 0, 1] + [1, 1, 1, 1, 1] + [1, 1, 1, 1, 1, 0, 0, 1, 1, 1] * 2  # 28/30 > 10/12 > 0.886
parameters[14, 2] = ('A2', 0, 0, 'B', 'D', None)

parameters[15, 0] = [3, 2, 3, 2, 3] + [2, 2, 2, 2, 2, 3, 3, 3, 3, 3] * 2 + [2, 2, 2, 2, 2]
parameters[15, 1] = [0, 1, 0, 1, 0] + [1, 1, 1, 1, 1, 0, 0, 1, 1, 1] * 2 + [1, 1, 1, 1, 1]  # 17/17 > 28/30
parameters[15, 2] = ('A2', 0, 0, 'A', 'D', None)"""