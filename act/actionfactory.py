from asbuilder import ASBuilder
from pdgbuilder import PDGBuilder
from bcbuilder import BCBuilder
from cluster import Cluster
from actiontype import ActionType
from featureextractor import FeatureExtractor
from astbuilder import ASTBuilder
from getstatistics import GetStatistics
from queryinconsistency import QueryInconsistency


class ActionFactory:

    def __init__(self, arguments):
        self.arguments = arguments
        self.action = None

    def perform_actions(self):

        for action in self.arguments.actions:
            if action == ActionType.AST.name:
                print '======================================='
                print '| Retrieve ASTs from the source codes |'
                print '======================================='
                self.start(ASTBuilder(arguments=self.arguments))
            elif action == ActionType.BC.name:
                print '======================================='
                print '|  Retrieve bc from the source codes  |'
                print '======================================='
                self.start(BCBuilder(arguments=self.arguments))
            elif action == ActionType.PDG.name:
                print '======================================='
                print '| Retrieve PDG from the LLVM bitcodes |'
                print '======================================='
                self.start(PDGBuilder(arguments=self.arguments))
            elif action == ActionType.AS.name:
                print '======================================='
                print '|   Extract Abstract Slices from PDG  |'
                print '======================================='
                self.start(ASBuilder(arguments=self.arguments))
            elif action == ActionType.FE.name:
                print '======================================='
                print '|          Extract features           |'
                print '======================================='
                self.start(FeatureExtractor(arguments=self.arguments))
            elif action == ActionType.MC.name:
                print '======================================='
                print '|            Cluster samples          |'
                print '======================================='
                self.start(Cluster(arguments=self.arguments))
            elif action == ActionType.ST.name:
                print '======================================='
                print '|        Print Clusters stats         |'
                print '======================================='
                self.start(GetStatistics(arguments=self.arguments))
            elif action == ActionType.QI.name:
                print '======================================='
                print '|        Query Inconsistencies         |'
                print '======================================='
                self.start(QueryInconsistency(arguments=self.arguments))

    def start(self, action):
        action.start()

