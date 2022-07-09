from typing import Dict

from pywikibot import ItemPage
from pywikibot.site import DataSite


class WikidataItem:

    def __init__(self, site: DataSite, label_dict: Dict, description_dict: Dict):
        self.site = site
        self.label_dict = label_dict
        self.description_dict = description_dict

    def create_item_page(self) -> ItemPage:
        new_item = ItemPage(self.site)
        new_item.editLabels(labels=self.label_dict, summary=f"Setting new "
                                                            f"labels of item "
                                                            f"{self.label_dict}")
        # Add description here or in another function
        new_item.editDescriptions(descriptions=self.description_dict, summary=f"Setting new description {self.description_dict}")
        return new_item

