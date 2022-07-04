from typing import Dict

from pywikibot import ItemPage
from pywikibot.site import DataSite


class WikidataItem:

    def __init__(self, site: DataSite, label_dict: Dict):
        self.site = site
        self.label_dict = label_dict

    def create_item_page(self) -> ItemPage:
        new_item = ItemPage(self.site)
        new_item.editLabels(labels=self.label_dict, summary="Setting labels")
        # Add description here or in another function
        return new_item.getID()

