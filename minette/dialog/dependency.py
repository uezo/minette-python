""" Container class for components that DialogRouter/DialogServices depend """


class DependencyContainer:
    def __init__(self, dialog, dependency_rules=None, **defaults):
        # set default dependencies
        for k, v in defaults.items():
            setattr(self, k, v)
        # set dialog specific dependencies
        if dependency_rules:
            dialog_dependencies = dependency_rules.get(type(dialog))
            if dialog_dependencies:
                for k, v in dialog_dependencies.items():
                    setattr(self, k, v)
