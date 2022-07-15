from pywikibot import Claim, DataSite, ItemPage


class WikidataClaim:
    def __init__(self, data_site: DataSite, prop: str, item: str):
        self.data_site = data_site
        self.prop = prop
        self.item = item

    def set_new_claim(self) -> Claim:
        # set claim
        claim: Claim = Claim(self.data_site, self.prop)
        target: object = ItemPage(self.data_site, self.item)
        claim.setTarget(target)
        return claim
