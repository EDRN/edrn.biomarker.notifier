# encoding: utf-8

'''Classes'''


class Protocol(object):
    '''Protocols have identifiers (which uniquely identify them), ttles, and biomarkers (all text)'''

    def __init__(self, identifier, title, biomarkers):
        self.identifier, self.title, self.biomarkers = identifier, title, biomarkers

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __lt__(self, other):
        return self.identifier < other.identifier

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.identifier})>'
