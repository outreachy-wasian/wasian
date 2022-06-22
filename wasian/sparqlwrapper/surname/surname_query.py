#!/usr/local/bin/python3
import codecs
import json
import re
from typing import Any, Dict, Match, Pattern

import ads
import issue as issue
from ads import SearchQuery
from ads.search import Article
from pywikibot.data.sparql import SparqlQuery
from requests import get, Response
from yaml import safe_load

# outputfile = codecs.open('populate_family_names_cache.json', "w", "utf-8")


def get_surnames(sparql_file_path: str, file_mode: str):
    surname_sparql = open(sparql_file_path, file_mode).read()
    sparql_query_wrapper = SparqlQuery()
    query_result: Dict = sparql_query_wrapper.query(surname_sparql)
    # outputfile.write(query_result)
    # for result_items in query_result['results']['bindings']:
        # item_value: str = result_items['item']['value']
        # qid: str = item_value[item_value.find("Q"): len(item_value)]
        # item_label_xml_lang_value: str = result_items['itemLabel']['xml:lang']
        # item_label_value: str = result_items['itemLabel']['value']
        # print(qid, item_label_xml_lang_value, item_label_value)
        # Using first author to dedup search queries.
        # Using "," to separate author first and last names.
        # Using solr's wildcard "*" to match author middle and first names.
        # Query format: last name, first name
    response: Response = get("https://raw.githubusercontent.com/adsabs/adsabs-dev-api/master/openapi/parameters.yaml")
    yaml: Dict = safe_load(response.text)
    search_query: SearchQuery = SearchQuery(first_author=f"Tapia, *", fl=yaml["fl"]["schema"]["items"]["enum"])
    for article in search_query:
        for key, value in article.items():
            if hasattr(article, key) and value is not None:
                print(key, value)







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
    get_surnames("../../sparql/wikidata/queries/surname.sparql", "r")
