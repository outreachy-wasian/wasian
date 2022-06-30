from pywikibot import Claim, ItemPage, DataSite


class WikidataClaim:

    def __init__(self, data_site: DataSite, target: object, prop: str, item: str):
        self.data_site = data_site
        self.target = target
        self.prop = prop
        self.item = item

    def set_new_claim(self) -> Claim:
        # set claim
        claim: Claim = Claim(self.data_site, self.prop)
        target: object = ItemPage(self.data_site, self.item)
        claim.setTarget(target)
        return claim
