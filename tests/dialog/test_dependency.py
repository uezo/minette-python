import sys
import os
sys.path.append(os.pardir)

from minette.dialog import (
    DialogService,
    DialogRouter,
    DependencyContainer
)


class SobaDialogService(DialogService):
    pass


class UdonDialogService(DialogService):
    pass


class RamenDialogService(DialogService):
    pass


class MenDialogRouter(DialogRouter):
    pass


def test_dependency():
    # dependencies
    d1 = 1
    d2 = 2
    d3 = 3
    d4 = 4
    d5 = 5
    d6 = 6
    d7 = 7

    # define rules
    dependency_rules = {
        SobaDialogService: {"d1": d1, "d2": d2},
        UdonDialogService: {"d2": d2, "d3": d3},
        RamenDialogService: {"d3": d3, "d4": d4},
        MenDialogRouter: {"d4": d4, "d5": d5}
    }

    # dialog service
    soba_dep = DependencyContainer(SobaDialogService(), dependency_rules, d6=d6, d7=d7)
    # dependencies for soba
    assert soba_dep.d1 == 1
    assert soba_dep.d2 == 2
    # dependencies for all
    assert soba_dep.d6 == 6
    assert soba_dep.d7 == 7
    # dependencies not for soba
    assert hasattr(soba_dep, "d3") is False

    # dialog router
    men_dep = DependencyContainer(MenDialogRouter(), dependency_rules, d6=d6, d7=d7)
    # dependencies for men
    assert men_dep.d4 == 4
    assert men_dep.d5 == 5
    # dependencies for all
    assert men_dep.d6 == 6
    assert men_dep.d7 == 7
    # dependencies not for men
    assert hasattr(men_dep, "d1") is False
