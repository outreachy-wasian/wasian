from pywikibot import Site
from pywikibot.site import DataSite


class WikidataSite:

    def __init__(self, code: str, fam: str):
        self.code = code
        self.fam = fam

    # get_data_site: get and connect data site
    def get_data_site(self) -> DataSite:
        # connect site
        site = Site(code=self.code, fam=self.fam)
        repo = site.data_repository()
        return repo
