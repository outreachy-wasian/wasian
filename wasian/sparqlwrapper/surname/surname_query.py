#!/usr/local/bin/python3
import codecs
import json
import re
from typing import Any, Dict, Match, Pattern, List

import ads
import issue as issue
from ads import SearchQuery
from ads.search import Article
from pywikibot.data.sparql import SparqlQuery
from requests import get, Response
from yaml import safe_load
from json import loads

# outputfile = codecs.open('populate_family_names_cache.json', "w", "utf-8")


def get_surnames(surname_sparql_file_path: str, file_mode: str, remote_fl_url: str, fl_sparql_file_path: str, key_map_file_path: str):
    surname_sparql = open(surname_sparql_file_path, file_mode).read()

    fl_sparql = open(fl_sparql_file_path, file_mode).read()

    key_map_text = open(key_map_file_path, file_mode).read()
    key_map_json = loads(key_map_text)

    sparql_query_wrapper = SparqlQuery()
    # surname_query_result: Dict = sparql_query_wrapper.query(surname_sparql)
    fl_query_result: Dict = sparql_query_wrapper.query(fl_sparql)



    # for result_items in query_result['results']['bindings']:
        # surname_item_id = result_items['property']['value'].replace('http://www.wikidata.org/entity/', '')
        # item_label_xml_lang_value: str = result_items['itemLabel']['xml:lang']
        # item_label_value: str = result_items['itemLabel']['value']
        # print(surname_item_id, item_label_xml_lang_value, item_label_value)
        # Using first author to dedup search queries.
        # Using "," to separate author first and last names.
        # Using solr's wildcard "*" to match author middle and first names.
        # Query format: last name, first name
    response: Response = get(remote_fl_url)
    yaml: Dict = safe_load(response.text)
    search_field: List = yaml["fl"]["schema"]["items"]["enum"]
    # delete ADS internal items before querying
    search_field.remove('id')
    search_field.remove('links_data')
    search_query: SearchQuery = SearchQuery(first_author=f"John, *", fl=search_field)
    for article in search_query:
        for key, value in article.items():
            if hasattr(article, key) and value is not None:
                # repalce the key
                if key in key_map_json:
                    # map to wikidata key
                    key = key_map_json[key]
                for result_items in fl_query_result['results']['bindings']:
                    fl_item_id = result_items['item']['value'].replace('http://www.wikidata.org/entity/', '')
                    fl_item_label = result_items['itemLabel']['value']
                    if fl_item_label == key:
                        print(fl_item_label, value)
                        # if fl_item_alt_label.lower().__contains__(titled_key):
                        #     print(fl_item_alt_label)
                            # if re.findall(regex_titled_key, fl_item_label):
                    # print(key, value)







# search = re.compile("Banchero, .*")
# print(search)
# papers = list(ads.SearchQuery(author="Banchero"))
# for paper in papers:
#     print("article:")
#     print(paper.title)
#     print("author:")
#     print(paper.author)

# print(resultitem['item']['value'].replace('http://www.wikidata.org/entity/','') + ', ' + resultitem['itemLabel']['value'])
#     outputfile.write(resultitem['item']['value'].replace('http://www.wikidata.org/entity/','') + ',' + resultitem['itemLabel']['value']+"\n")

# outputfile.close()
# json_object = json.dumps(query_result, indent=4, ensure_ascii=False)\
#                 .encode('utf-8')
#
# with open("populate_family_names_cache3.json", "wb") as outfile:
#     outfile.write(json_object)

if __name__ == "__main__":  # pragma: no cover
    get_surnames("../../sparql/wikidata/queries/surname.sparql", "r", "https://raw.githubusercontent.com/adsabs/adsabs-dev-api/master/openapi/parameters.yaml", "../../sparql/wikidata/queries/list_of_solr_fields_on_ads.sparql", "./wikidata_key_replace_map.json")
