from enum import Enum


class ActionType(Enum):
    AST = 'Retrieve Abstract Syntax Tree'
    BC = 'Retrieve bitcode'
    PDG = 'Retrieve Program Dependence Graph'
    AS = 'Extract Abstract Forward Slices'
    FE = 'Feature Extraction'
    MC = 'Model Construction'
    ST = 'Get cluster statistics'
    QI = 'Query inconsistencies'

    @staticmethod
    def get_names():
        return [e.name for e in ActionType]

    @staticmethod
    def get_detail():
        return ['{}: {}'.format(e.name, e.value) for e in ActionType]
