from pywikibot import Claim, DataSite, ItemPage


class WikidataClaim:
    def __init__(self, data_site: DataSite, prop: str, item: str, target: any):
        self.data_site = data_site
        self.prop = prop
        self.item = item
        self.target = target

    def set_new_claim(self) -> Claim:
        # set claim
        claim: Claim = Claim(self.data_site, self.prop)
        claim.setTarget(self.target)
        return claim
