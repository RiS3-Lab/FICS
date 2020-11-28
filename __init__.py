import sys

from act.actionfactory import ActionFactory
from argsparser import ArgsParser

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    args_parser = ArgsParser()
    args_parser.parse()
    args_parser.do_basic_checks()
    ActionFactory(args_parser.arguments).perform_actions()
