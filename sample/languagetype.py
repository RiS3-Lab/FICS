from enum import Enum


class LanguageType(Enum):
    C = 'C'

    @staticmethod
    def get_names():
        return [e.name for e in LanguageType]

    @staticmethod
    def get_detail():
        return ['{}: {}'.format(e.name, e.value) for e in LanguageType]
