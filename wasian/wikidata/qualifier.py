from pywikibot import Claim, DataSite


class WikidataQualifier:

    def __init__(self, data_site: DataSite, target: object, prop: str):
        self.data_site = data_site
        self.target = target
        self.prop = prop

    def set_qualifier_targets(self) -> Claim:
        # set qualifier
        qualifier: Claim = Claim(self.data_site, self.prop)
        qualifier.setTarget(self.target)
        return qualifier
