#!/usr/local/bin/python3
import codecs
import json
import re
import sys
from difflib import SequenceMatcher
from json import loads
from typing import Any, AnyStr, Dict, List, Match, Pattern

import ads
import issue as issue
from ads import SearchQuery
from ads.search import Article
from dateutil.parser import parse
from pywikibot.data.sparql import SparqlQuery
from requests import Response, get
from yaml import safe_load

sys.path.append("../../../")

from pywikibot import Claim, ItemPage, Site, WbQuantity, WbTime
from pywikibot.exceptions import InvalidTitleError
from pywikibot.site import DataSite

from wasian.wikidata.claim import WikidataClaim
from wasian.wikidata.item import WikidataItem
from wasian.wikidata.qualifier import WikidataQualifier
from wasian.wikidata.site import WikidataSite

result = {
    "results": {
        "bindings": [{"item": {"value": ""}, "itemLabel": {"value": ""}}]
    },
}
title_value = ""
orcid_pub_list = []
url_prefix = "http://www.wikidata.org/entity/"
name_separator = ", "
approximately_string_matching_rate = 0.9

# outputfile = codecs.open('populate_family_names_cache.json', "w", "utf-8")


def get_surnames(
    surname_sparql_file_path: str,
    file_mode: str,
    remote_fl_url: str,
    fl_sparql_file_path: str,
    key_map_file_path: str,
    search_item_file_path: str,
    search_doi_file_path: str,
    search_item_with_instance_family_name_file_path: str,
    search_item_with_instance_given_name_file_path: str,
    search_publication_file_path: str,
    search_orcid_id_file_path: str,
):
    global result, title_value, orcid_pub_list

    fl_sparql = open(fl_sparql_file_path, file_mode).read()
    surname_sparql = open(surname_sparql_file_path, file_mode).read()
    search_item_sparql = open(search_item_file_path, file_mode).read()
    search_doi_sparql = open(search_doi_file_path, file_mode).read()
    search_publication_sparql = open(
        search_publication_file_path, file_mode
    ).read()
    search_item_with_instance_family_name_sparql = open(
        search_item_with_instance_family_name_file_path, file_mode
    ).read()
    search_item_with_instance_given_name_sparql = open(
        search_item_with_instance_given_name_file_path, file_mode
    ).read()
    search_orcid_id_sparql = open(search_orcid_id_file_path, file_mode).read()

    key_map_text = open(key_map_file_path, file_mode).read()
    key_map_json = loads(key_map_text)

    sparql_query_wrapper = SparqlQuery()
    # surname_query_result: Dict = sparql_query_wrapper.query(surname_sparql)

    # for result_items in surname_query_result['results']['bindings']:
    #     surname_item_id = result_items['item']['value'].replace(url_prefix, '')
    #     item_label_xml_lang_value: str = result_items['itemLabel']['xml:lang']
    #     item_label_value: str = result_items['itemLabel']['value']
    #     print(surname_item_id, item_label_xml_lang_value, item_label_value)

    # Using first author to dedup search queries.
    # Using "," to separate author first and last names.
    # Using solr's wildcard "*" to match author middle and first names.
    # Query format: last name, first name
    response: Response = get(remote_fl_url)
    yaml: Dict = safe_load(response.text)
    search_field: List = yaml["fl"]["schema"]["items"]["enum"]
    # delete ADS internal items before querying
    search_field.remove("id")
    search_field.remove("links_data")
    # query by first author surname in English, de-duping over-query
    # search_query: SearchQuery = SearchQuery(first_author=f"{item_label_value}, *", fl=search_field)
    search_query: SearchQuery = SearchQuery(
        bibcode="1953Natur.171..737W", fl=search_field
    )

    wikidata_site = WikidataSite("wikidata", "wikidata")
    data_site = wikidata_site.get_data_site()

    # iterate over all results
    for article in search_query:
        if article.orcid_pub:
            orcid_pub_list = article.orcid_pub
            print(orcid_pub_list)
        # search doi in ADS
        if article.doi:
            print("doi: ", article.doi)
            doi: str = article.doi[0]
            doi_uppercase = doi.upper()
            search_doi_query = search_doi_sparql % (doi_uppercase)
            result = sparql_query_wrapper.query(search_doi_query)
            if result["results"]["bindings"][0]["boolean"]["value"] == "true":
                print("already exists")
                search_and_add_statement(
                    article,
                    key_map_json,
                    data_site,
                    sparql_query_wrapper,
                    fl_sparql,
                    search_item_with_instance_given_name_sparql,
                    search_item_with_instance_family_name_sparql,
                    search_publication_sparql,
                    search_orcid_id_sparql,
                )
            else:
                print(f"does not exist")
                # title = article.title[0]
                # description = "scientific article published in January 2019"
                # item = create_wikidata_item_page('en', title, description, data_site)
                # print(item.getID())
        # if doi isn't available in ADS, search title in ADS
        else:
            print("title: ", article.title)
            title: str = article.title[0]
            search_title_query = search_item_sparql % (title)
            result = sparql_query_wrapper.query(search_title_query)
            if result["results"]["bindings"]:
                print("already exists")
                search_and_add_statement(
                    article,
                    key_map_json,
                    data_site,
                    sparql_query_wrapper,
                    fl_sparql,
                    search_item_with_instance_given_name_sparql,
                    search_item_with_instance_family_name_sparql,
                    search_publication_sparql,
                    search_orcid_id_sparql,
                )
            else:
                print(f"does not exist")

                # item_page = ItemPage(data_site, item)
                # if fl_item_alt_label.lower().__contains__(titled_key):
                #     print(fl_item_alt_label)
                # if re.findall(regex_titled_key, fl_item_label):
                # print(key, value)

        # Claim(data_site, fl_item_id).setTarget(value[0])

        # wikidata_claim = WikidataClaim(data_site, value, fl_item_id, "Q225445")
        # claim = wikidata_claim.set_new_claim()
        # wikidata_qualifier = WikidataQualifier(data_site, value, fl_item_id)
        # qualifier = wikidata_qualifier.set_qualifier_targets()
        # claim.addQualifier(qualifier)
    # return claim


# search = re.compile("Banchero, .*")
# print(search)
# papers = list(ads.SearchQuery(author="Banchero"))
# for paper in papers:
#     print("article:")
#     print(paper.title)
#     print("author:")
#     print(paper.author)

# print(resultitem['item']['value'].replace(url_prefix,'') + ', ' + resultitem['itemLabel']['value'])
#     outputfile.write(resultitem['item']['value'].replace(url_prefix,'') + ',' + resultitem['itemLabel']['value']+"\n")

# outputfile.close()
# json_object = json.dumps(query_result, indent=4, ensure_ascii=False)\
#                 .encode('utf-8')
#
# with open("populate_family_names_cache3.json", "wb") as outfile:
#     outfile.write(json_object)


def search_and_add_statement(
    article,
    key_map_json,
    data_site,
    sparql_query_wrapper,
    fl_sparql,
    search_item_with_instance_given_name_sparql,
    search_item_with_instance_family_name_sparql,
    search_publication_sparql,
    search_orcid_id_sparql,
):
    # key value a pair of articles
    for key, value in article.items():
        # ensure it has a key and the value isn't empty
        if hasattr(article, key) and value is not None:
            # repalce the key
            if key in key_map_json:
                # map to wikidata key
                key: str = key_map_json[key]
            # query dict
            fl_query_result: Dict = sparql_query_wrapper.query(fl_sparql)
            for result_items in fl_query_result["results"]["bindings"]:
                fl_item_id: str = result_items["item"]["value"].replace(
                    url_prefix, ""
                )
                fl_item_label: str = result_items["itemLabel"]["value"]
                if fl_item_label.casefold() == key.casefold():
                    print(fl_item_id, fl_item_label, value)
                    # add claim to item
                    item = ItemPage(data_site, "Q1895685")
                    # item_id = result['results']['bindings'][0]['item']['value'].replace(url_prefix,'')
                    if fl_item_id == "P1104":
                        wb_quant = WbQuantity(
                            value,
                            ItemPage(data_site, "Q1069725"),
                            site=data_site,
                        )
                        if not search_if_the_statement_exists_string(
                            item, fl_item_id, wb_quant
                        ):
                            claim = Claim(data_site, fl_item_id)
                            claim.setTarget(wb_quant)
                            print(claim)
                            # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                    elif fl_item_id == "P577":
                        if not search_if_the_statement_exists(
                            item, fl_item_id
                        ):
                            date_time = parse(value)
                            wb_time = WbTime(
                                year=date_time.year,
                                month=date_time.month,
                                site=data_site,
                            )
                            claim = Claim(data_site, fl_item_id)
                            claim.setTarget(wb_time)
                            print(claim)
                            # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                    elif fl_item_id == "P304":
                        if item.claims[fl_item_id]:
                            pages_str = f"{value}, {item.claims[fl_item_id][0].getTarget()}"
                            result = sub_hyphen_in_pages(pages_str)
                            page_raw = result.split(", ")
                            ads_page = page_raw[0].replace(" ", "")
                            wikidata_page = page_raw[1].replace(" ", "")
                            if ads_page != wikidata_page:
                                claim = Claim(data_site, fl_item_id)
                                claim.setTarget(value)
                                print(claim)
                                # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                            else:
                                print(
                                    f"{page_raw[0]} is equal to {page_raw[1]}"
                                )
                        else:
                            print(f"{fl_item_id} is not found on wikidata")
                            claim = Claim(data_site, fl_item_id)
                            claim.setTarget(value)
                            print(claim)
                            # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                    elif fl_item_id == "P1433":
                        if not search_if_the_statement_exists_item(
                            item, data_site, fl_item_id, value
                        ):
                            publication_query = search_publication_sparql % (
                                value
                            )
                            result = sparql_query_wrapper.query(
                                publication_query
                            )
                            if result["results"]["bindings"]:
                                qid = result["results"]["bindings"][0]["item"][
                                    "value"
                                ].replace(url_prefix, "")
                                print(qid)
                                target = ItemPage(data_site, qid)
                                claim = Claim(data_site, fl_item_id)
                                claim.setTarget(target)
                                print(claim)
                                # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                            else:
                                print(f"{value} not found")
                    elif fl_item_id == "P2093":
                        # TODO: move this to related author properties
                        author_item_ids = ["P50", fl_item_id]
                        wikidata_author_list = (
                            sort_authors_and_return_a_sorted_list(
                                item, data_site, author_item_ids
                            )
                        )
                        ads_author_regex_list = (
                            format_author_list_from_ads_in_regex(value)
                        )
                        # two lists are same, add properties
                        if len(wikidata_author_list) == len(
                            ads_author_regex_list
                        ):
                            no_matched_ads_value = [
                                ads_value
                                for ads_value, wikidata_value in zip(
                                    ads_author_regex_list, wikidata_author_list
                                )
                                if not match_author_regex(
                                    ads_value, wikidata_value
                                )
                            ]
                            print(
                                f"those are not matched: {no_matched_ads_value}"
                            )
                            # 1: the series ordinal is wrong. 2: author not present on Wikidata
                            if no_matched_ads_value:
                                while no_matched_ads_value:
                                    # in case if series ordinal is wrong on Wikidata, rematch
                                    for v in no_matched_ads_value:
                                        for i in wikidata_author_list:
                                            if match_author_regex(v, i):
                                                print(f"matched {v} to {i}")
                                                no_matched_ads_value.remove(v)
                            print(f"after cleared: {no_matched_ads_value}")
                        else:
                            # TODO compute lists from regex
                            # find if there are missing authors on Wikidata
                            ads_author_list = format_author_list_from_ads(
                                value
                            )
                            wikidata_author_set = set(wikidata_author_list)
                            ads_author_set = set(ads_author_list)
                            missing_author_names_from_ads = list(
                                sorted(ads_author_set - wikidata_author_set)
                            )
                            print(
                                f"missing author from ads: {missing_author_names_from_ads}"
                            )
                            if missing_author_names_from_ads:
                                for index, name in enumerate(
                                    missing_author_names_from_ads
                                ):
                                    # try to look at orcid
                                    if orcid_pub_list[index] != "-":
                                        print(name, orcid_pub_list[index])
                                        # search if an orcid id exists on wikidata
                                        search_orcid_query = (
                                            search_orcid_id_sparql
                                            % (orcid_pub_list[index])
                                        )
                                        result = sparql_query_wrapper.query(
                                            search_orcid_query
                                        )
                                        print(result)
                                        # found orcid id on wikidata, add author statement to article
                                        if result["results"]["bindings"]:
                                            print("orcid already exists")
                                            # expect 1 result means there's only one orcid on wikidata
                                            author_item_id = result["results"][
                                                "bindings"
                                            ][0]["item"]["value"].replace(
                                                url_prefix, ""
                                            )
                                            target = ItemPage(
                                                data_site, author_item_id
                                            )
                                            author_claim = Claim(
                                                data_site, "P50"
                                            )
                                            author_claim.setTarget(target)
                                            # item.addClaim(author_claim, summary=f'Adding claim "P50" to Q225445')
                                        # orcid id not found on wikidata, but exists in ADS, create author item and add related orcid to wikidata
                                        else:
                                            # step 1: create author item
                                            # author_item = create_wikidata_item_page('en', author_name, f"researcher, ORCID iD = {orcid_pub_list[index]}", data_site)
                                            # print(author_item.getID())
                                            # add instance of Q5 to author item
                                            instance_of_claim = Claim(
                                                data_site, "P31"
                                            )
                                            instance_of_claim.setTarget(
                                                ItemPage(data_site, "Q5")
                                            )
                                            # split author name into first and last name
                                            author_name_split = (
                                                split_author_name(v)
                                            )
                                            print(author_name_split)
                                            # search with given name item with initials
                                            search_given_name_query = (
                                                search_item_with_instance_given_name_sparql
                                                % (author_name_split[1])
                                            )
                                            result = (
                                                sparql_query_wrapper.query(
                                                    search_given_name_query
                                                )
                                            )
                                            if result["results"]["bindings"]:
                                                # add given name string claim to author item
                                                given_name_claim = Claim(
                                                    data_site, "P735"
                                                )
                                                given_name_item = result[
                                                    "results"
                                                ]["bindings"][0]["item"][
                                                    "value"
                                                ].replace(
                                                    url_prefix, ""
                                                )
                                                given_name_claim.setTarget(
                                                    ItemPage(
                                                        data_site,
                                                        given_name_item,
                                                    )
                                                )
                                                # author_item.addClaim(given_name_claim, summary=f'Adding claim "P735" to {author_item}')
                                            # search with family name item
                                            search_family_name_query = (
                                                search_item_with_instance_family_name_sparql
                                                % (author_name_split[0])
                                            )
                                            result = (
                                                sparql_query_wrapper.query(
                                                    search_family_name_query
                                                )
                                            )
                                            if result["results"]["bindings"]:
                                                # add family name claim to author item
                                                family_name_claim = Claim(
                                                    data_site, "P734"
                                                )
                                                family_name_item = result[
                                                    "results"
                                                ]["bindings"][0]["item"][
                                                    "value"
                                                ].replace(
                                                    url_prefix, ""
                                                )
                                                family_name_claim.setTarget(
                                                    ItemPage(
                                                        data_site,
                                                        family_name_item,
                                                    )
                                                )
                                                # author_item.addClaim(family_name_claim, summary=f'Adding claim "P734" to {author_item}')
                                            # add orcid claim to author item
                                            orcid_claim = Claim(
                                                data_site, "P496"
                                            )
                                            orcid_claim.setTarget(
                                                orcid_pub_list[index]
                                            )
                                            # add occupation associated to orcid
                                            occupation_claim = Claim(
                                                data_site, "P106"
                                            )
                                            occupation_claim.setTarget(
                                                ItemPage(data_site, "Q1650915")
                                            )
                                            # add claims to author item
                                            # author_item.addClaim(instance_of_claim, summary=f'Adding claim "P31" to {author_item}')
                                            # author_item.addClaim(orcid_claim, summary=f'Adding claim "P496" to {author_item}')
                                            # author_item.addClaim(occupation_claim, summary=f'Adding claim "P106" to {author_item}')
                                            # step 2: add author item to article
                                            # target = ItemPage(data_site, author_item.getID())
                                            # author_claim = Claim(data_site, "P50")
                                            # author_claim.setTarget(target)
                                            # item.addClaim(author_claim, summary=f'Adding claim "P50" to Q225445')
                                    # orcid id not found in ADS, add author name string to article
                                    else:
                                        claim = Claim(data_site, fl_item_id)
                                        claim.setTarget(name)
                                        print(claim)
                                        # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q63380831')
                    else:
                        if type(value) is str:
                            if not search_if_the_statement_exists_string(
                                item, fl_item_id, value
                            ):
                                claim = Claim(data_site, fl_item_id)
                                claim.setTarget(value)
                                print(claim)
                                # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')
                        else:
                            for v in value:
                                if not search_if_the_statement_exists_string(
                                    item, fl_item_id, v
                                ):
                                    claim = Claim(data_site, fl_item_id)
                                    claim.setTarget(str(v))
                                    print(claim)
                                    # item.addClaim(claim, summary=f'Adding claim {fl_item_id} to Q225445')


"""
try to find same statement regex, if exists, skip
"""


def search_if_the_statement_exists_regex(
    item, data_site, author_item_ids, value
) -> bool:
    for author_item_id in author_item_ids:
        try:
            for claim in item.claims[author_item_id]:
                target = claim.getTarget()
                try:
                    # get item title from target
                    target_label = get_label_from_target(target, data_site)
                    print(target_label)
                    print(value)
                    return match_author_regex(value, target_label)
                except InvalidTitleError:
                    print(target)
                    print(value)
                    return match_author_regex(value, target)
        except KeyError:
            print(f"{author_item_id} not found")


"""
sort authors and numbered qualifiers
"""


def sort_authors_and_return_a_sorted_list(
    item, data_site, author_item_ids
) -> list:
    author_dict = {}
    for author_item_id in author_item_ids:
        try:
            for claim in item.claims[author_item_id]:
                if "P1545" in claim.qualifiers:
                    for qual in claim.qualifiers[
                        "P1545"
                    ]:  # iterate over all P1545
                        number = qual.target
                        target = claim.getTarget()
                        try:
                            # get item title from target
                            target_label = get_label_from_target(
                                target, data_site
                            )
                            print(number)
                            print(target_label)
                            author_dict[number] = target_label
                        except InvalidTitleError:
                            print(number)
                            print(target)
                            author_dict[number] = target
        except KeyError:
            pass
    print(author_dict)
    sorted_author_dict: Dict = dict(
        sorted(author_dict.items(), key=lambda x: int(x[0]))
    )
    print(sorted_author_dict)
    sorted_author_list: List = list(sorted_author_dict.values())
    print(sorted_author_list)
    return sorted_author_list


def format_author_list_from_ads_in_regex(value) -> list:
    author_ads_regex_list = []
    for v in value:
        # skip if there are other strings e.g. collaboration
        # in the author name
        if name_separator in v:
            author_name_regex = put_author_name_in_regex(v)
            author_ads_regex_list.append(author_name_regex)
    return author_ads_regex_list


def format_author_list_from_ads(value) -> list:
    author_ads_list = []
    for v in value:
        # skip if there are other strings e.g. collaboration
        # in the author name
        if name_separator in v:
            author_name = format_author_name(v)
            author_ads_list.append(author_name)
    return author_ads_list


"""
try to find same statement string, if exists, skip
"""


def match_author_regex(author_regex, target) -> bool:
    matched = re.search(rf"{author_regex}", target)
    if matched:
        return True


"""
try to find same statement string, if exists, skip
"""


def search_if_the_statement_exists_string(item, fl_item_id, value) -> bool:
    try:
        for claim in item.claims[fl_item_id]:
            print(claim.getTarget())
            print(value)
            print(f"{claim.getTarget().casefold()}" == f"{value.casefold()}")
            if claim.getTarget().casefold() == value.casefold():
                print(
                    f"{fl_item_id} already exists, its value:",
                    claim.getTarget(),
                )
                return True
    except KeyError:
        print(f"{fl_item_id} not found, do not skip")


"""
try to find same statement item, if exists, skip
"""


def search_if_the_statement_exists_item(
    item, data_site, fl_item_id, value
) -> bool:
    try:
        for claim in item.claims[fl_item_id]:
            target = claim.getTarget()
            # get item title from target
            target_label = get_label_from_target(target, data_site)
            if target_label.casefold() == value.casefold():
                print(f"{fl_item_id} already exists, its value:", value)
                return True
    except KeyError:
        print(f"{fl_item_id} not found, do not skip")


"""
try to find same statement item, if exists, skip
"""


def search_if_the_statement_exists(item, fl_item_id) -> bool:
    try:
        if item.claims[fl_item_id]:
            print(f"{fl_item_id} already exists")
            return True
    except KeyError:
        print(f"{fl_item_id} not found, do not skip")


def get_label_from_target(target, data_site):
    # get item title from target
    title = target.title()
    title_page = ItemPage(data_site, title)
    target_label = title_page.get()["labels"]["en"]
    return target_label


def create_wikidata_item_page(
    lang: str, title: str, description: str, data_site: DataSite
) -> ItemPage:
    wikidata_item = WikidataItem(data_site, {lang: title}, {lang: description})
    new_item_page = wikidata_item.create_item_page()
    return new_item_page


def add_affiliation_to_author_item(author_item_id, affiliation):
    wikidata_site = WikidataSite("wikidata", "wikidata")
    data_site = wikidata_site.get_data_site()
    item = ItemPage(data_site, author_item_id)
    claim = Claim(data_site, "P2093")
    claim.setTarget(affiliation)
    # item.addClaim(claim, summary=f'Adding claim "P2093" to Q225445')


def put_author_name_in_regex(author) -> str:
    # split author first and last name
    names = split_author_name(author)
    # attract each abbrev by whitespace
    abbrevs = names[1].split(" ")
    # attract first name
    first_name = abbrevs[0]
    # get first char
    first_char = first_name[0]
    # construct regex for first abbrev
    first_name_abbrev_regex = f"{first_char}.*"
    # get author last names
    author_last_names = names[0]
    # join first and last names together
    full_name_in_regex_format = (
        first_name_abbrev_regex + " " + author_last_names
    )
    # return full name
    return full_name_in_regex_format


def format_author_name(author) -> str:
    # split author first and last name
    names = split_author_name(author)
    # get author first and last names
    author_first_name = names[1]
    author_last_name = names[0]
    # join first and last names together
    full_name_in_wikidata_format = author_first_name + " " + author_last_name
    # return full name
    return full_name_in_wikidata_format


def split_author_name(author) -> list:
    # split author first and last name
    names = author.split(name_separator)
    return names


def sub_hyphen_in_pages(sub_str):
    hyphen_regex = r"[\u002D\u058A\u05BE\u1400\u1806\u2010-\u2015\u2E17\u2E1A\u2E3A\u2E3B\u2E40\u301C\u3030\u30A0\uFE31\uFE32\uFE58\uFE63\uFF0D]"
    subst = ""
    # You can manually specify the number of replacements by changing the 4th argument
    result = re.sub(hyphen_regex, subst, sub_str, 0, re.IGNORECASE)
    if result:
        return result


if __name__ == "__main__":  # pragma: no cover
    get_surnames(
        "../../sparql/wikidata/queries/surname.sparql",
        "r",
        "https://raw.githubusercontent.com/adsabs/adsabs-dev-api/master/openapi/parameters.yaml",
        "../../../sparql/wikidata/queries/list_of_solr_fields_on_ads.sparql",
        "../wikidata_key_replace_map.json",
        "../../../sparql/wikidata/queries/search_if_an_item_exists.sparql",
        "../../../sparql/wikidata/queries/search_if_a_doi_exists.sparql",
        "../../../sparql/wikidata/queries/search_an_item_with_instance_of_family_name.sparql",
        "../../../sparql/wikidata/queries/search_an_item_with_instance_of_given_name.sparql",
        "../../../sparql/wikidata/queries/search_if_a_publication_exists.sparql",
        "../../../sparql/wikidata/queries/search_if_an_orcid_id_exists.sparql",
    )
