#!/usr/local/bin/python3
import sys
from datetime import date
from json import loads
from typing import Dict, List

from ads import SearchQuery
from bs4 import BeautifulSoup
from dateutil.parser import parse
from pywikibot.data.sparql import SparqlQuery
from requests import Response, get
from yaml import safe_load

sys.path.append("../../../")

from pywikibot import Claim, ItemPage, WbMonolingualText, WbQuantity, WbTime
from pywikibot.site import DataSite

from wasian.tools.mlstripper import MLStripper
from wasian.wikidata.item import WikidataItem
from wasian.wikidata.site import WikidataSite

url_prefix = "http://www.wikidata.org/entity/"
name_separator = ", "
arxiv_identifier = "arXiv"
affiliation_separator = "; "
empty_value = "-"

# Using surnames from Wikidata as key to search articles in ADS database, import scholarly articles and create Wikidata items.
def import_from_ads(
    surname_sparql_file_path: str,
    file_mode: str,
    remote_fl_url: str,
    fl_sparql_file_path: str,
    key_map_file_path: str,
    search_doi_file_path: str,
    search_item_with_instance_family_name_file_path: str,
    search_item_with_instance_given_name_file_path: str,
    search_orcid_id_file_path: str,
    search_ads_bibcode_file_path: str,
    search_issn_file_path: str,
):
    # read sparql files
    fl_sparql = open(fl_sparql_file_path, file_mode).read()
    surname_sparql = open(surname_sparql_file_path, file_mode).read()
    search_doi_sparql = open(search_doi_file_path, file_mode).read()
    search_item_with_instance_family_name_sparql = open(
        search_item_with_instance_family_name_file_path, file_mode
    ).read()
    search_item_with_instance_given_name_sparql = open(
        search_item_with_instance_given_name_file_path, file_mode
    ).read()
    search_orcid_id_sparql = open(search_orcid_id_file_path, file_mode).read()
    search_ads_bibcode_sparql = open(
        search_ads_bibcode_file_path, file_mode
    ).read()
    search_issn_sparql = open(search_issn_file_path, file_mode).read()

    key_map_text = open(key_map_file_path, file_mode).read()
    key_map_json = loads(key_map_text)

    sparql_query_wrapper = SparqlQuery()
    surname_query_result: Dict = sparql_query_wrapper.query(surname_sparql)

    for result_items in surname_query_result["results"]["bindings"]:
        surname_item_id = result_items["item"]["value"].replace(url_prefix, "")
        item_label_xml_lang_value: str = result_items["itemLabel"]["xml:lang"]
        item_label_value: str = result_items["itemLabel"]["value"]
        print(surname_item_id, item_label_xml_lang_value, item_label_value)

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
        search_query: SearchQuery = SearchQuery(
            first_author=f"{item_label_value}, *", fl=search_field
        )

        # connect wikidata site
        wikidata_site = WikidataSite("wikidata", "wikidata")
        data_site = wikidata_site.get_data_site()

        # iterate over all results
        for article in search_query:
            # search doi in ADS
            if article.doi:
                print("doi: ", article.doi)
                doi: str = article.doi[0]
                search_doi_query = search_doi_sparql % (doi)
                doi_uppercase = doi.upper()
                search_doi_uppercase_query = search_doi_sparql % (
                    doi_uppercase
                )
                doi_result = sparql_query_wrapper.query(search_doi_query)
                doi_uppercase_result = sparql_query_wrapper.query(
                    search_doi_uppercase_query
                )
                if (
                    doi_result["results"]["bindings"][0]["boolean"]["value"]
                    == "true"
                    or doi_uppercase_result["results"]["bindings"][0][
                        "boolean"
                    ]["value"]
                    == "true"
                ):
                    print(f"{doi} already exists, don't do anything")
                else:
                    print(f"{doi} does not exist on wikidata, creating item")
                    (
                        orcid_pub_list,
                        affiliation_list,
                        arxiv_class_list,
                    ) = define_refreshable_lists(article)
                    create_article_item(
                        article,
                        data_site,
                        key_map_json,
                        sparql_query_wrapper,
                        fl_sparql,
                        search_item_with_instance_given_name_sparql,
                        search_item_with_instance_family_name_sparql,
                        search_issn_sparql,
                        search_orcid_id_sparql,
                        orcid_pub_list,
                        affiliation_list,
                        arxiv_class_list,
                    )
            # if doi isn't available in ADS, search ADS bibcode in ADS database
            else:
                print("ADS bibcode: ", article.bibcode)
                ads_bibcode: str = article.bibcode
                search_ads_bibcode_query = search_ads_bibcode_sparql % (
                    ads_bibcode
                )
                result = sparql_query_wrapper.query(search_ads_bibcode_query)
                if (
                    result["results"]["bindings"][0]["boolean"]["value"]
                    == "true"
                ):
                    print(f"{ads_bibcode} already exists, don't do anything")
                else:
                    print(
                        f"{ads_bibcode} does not exist on wikidata, creating item"
                    )
                    (
                        orcid_pub_list,
                        affiliation_list,
                        arxiv_class_list,
                    ) = define_refreshable_lists(article)
                    create_article_item(
                        article,
                        data_site,
                        key_map_json,
                        sparql_query_wrapper,
                        fl_sparql,
                        search_item_with_instance_given_name_sparql,
                        search_item_with_instance_family_name_sparql,
                        search_issn_sparql,
                        search_orcid_id_sparql,
                        orcid_pub_list,
                        affiliation_list,
                        arxiv_class_list,
                    )


# create item about scholarly articles
def create_article_item(
    article,
    data_site,
    key_map_json,
    sparql_query_wrapper,
    fl_sparql,
    search_item_with_instance_given_name_sparql,
    search_item_with_instance_family_name_sparql,
    search_issn_sparql,
    search_orcid_id_sparql,
    orcid_pub_list,
    affiliation_list,
    arxiv_class_list,
):
    # get title of article
    title = article.title[0]
    # get date of article
    date = article.date
    # process title and description
    striped_title = strip_html_tags_from_title(title)
    print(f"title: {striped_title}")
    description = compose_description_from_date(date)
    print(f"description: {description}")
    item = create_wikidata_item_page(
        "en", striped_title, description, data_site
    )
    item_id = item.getID()
    print(f"new article item: {url_prefix}{item_id}")
    search_and_add_statement_from_ads(
        item,
        item_id,
        article,
        key_map_json,
        data_site,
        sparql_query_wrapper,
        fl_sparql,
        search_item_with_instance_given_name_sparql,
        search_item_with_instance_family_name_sparql,
        search_issn_sparql,
        search_orcid_id_sparql,
        orcid_pub_list,
        affiliation_list,
        arxiv_class_list,
    )


# detect_if_title_contains_html_tag
def detect_if_title_contains_html_tag(title: str) -> bool:
    return bool(BeautifulSoup(title, "html.parser").find())


# strip title of html tags
def strip_html_tags_from_title(title):
    s = MLStripper()
    s.feed(title)
    return s.get_data()


# compose description of scholarly articles
def compose_description_from_date(date: str) -> str:
    if date:
        date_time = parse(date)
        return f"scholarly article published in {date_time.strftime('%B %Y')}"
    else:
        return "scholarly article"


# define refreshable lists
def define_refreshable_lists(article):
    # define refreshable lists
    orcid_pub_list = []
    affiliation_list = []
    arxiv_class_list = []
    # get orcid id to list
    if article.orcid_pub:
        orcid_pub_list = article.orcid_pub
        print(f"public orcid id list: {orcid_pub_list}")
    # get affiliation string to list
    if article.aff:
        affiliation_list = article.aff
        print(f"affiliation list: {affiliation_list}")
    # get arxiv classification to list
    if article.arxiv_class:
        arxiv_class_list = article.arxiv_class
        print(f"arxiv class list: {arxiv_class_list}")
    return orcid_pub_list, affiliation_list, arxiv_class_list


# Automatically search and add statements from ADS
def search_and_add_statement_from_ads(
    item: ItemPage,
    item_id: str,
    article,
    key_map_json,
    data_site,
    sparql_query_wrapper,
    fl_sparql,
    search_item_with_instance_given_name_sparql,
    search_item_with_instance_family_name_sparql,
    search_issn_sparql,
    search_orcid_id_sparql,
    orcid_pub_list,
    affiliation_list,
    arxiv_class_list,
):
    # Manually add P31 (instance of) statement to wikidata item
    # Q13442814 is scholarly article id
    scholarly_article_page = ItemPage(data_site, "Q13442814")
    create_a_claim(data_site, "P31", scholarly_article_page, item, item_id)

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

                    # get bibcode from ADS
                    bibcode: str = article.bibcode

                    if fl_item_id == "P818":
                        arxiv_ids = filter_arxiv_ids_from_alternate_bibcodes(
                            value
                        )
                        # lists all arxiv ids, though expecting only one is used
                        for arxiv_id in arxiv_ids:
                            arxiv_digits = extract_arxiv_digits_from_arxiv_id(
                                arxiv_id
                            )
                            print(f"arXiv ID: {arxiv_digits}")
                            claim = create_a_claim(
                                data_site,
                                fl_item_id,
                                arxiv_digits,
                                item,
                                item_id,
                            )
                            # add arxiv classification to P820, there might be multiple classes in one arxiv id
                            for arxiv_class in arxiv_class_list:
                                add_qualifiers_to_claim(
                                    data_site, "P820", arxiv_class, claim
                                )
                            # add sources to claim
                            article_sources = (
                                construct_sources_to_article_claim(
                                    data_site, bibcode
                                )
                            )
                            add_sources_to_claim(article_sources, claim)
                    elif fl_item_id == "P236":
                        for v in value:
                            issn_query = search_issn_sparql % (v)
                            result = sparql_query_wrapper.query(issn_query)
                            if result["results"]["bindings"]:
                                # expect there's only one result of journal
                                journal_item_id = result["results"][
                                    "bindings"
                                ][0]["item"]["value"].replace(url_prefix, "")
                                print(
                                    f"journal item id: {url_prefix}{journal_item_id}"
                                )
                                journal_item_page = ItemPage(
                                    data_site, journal_item_id
                                )
                                published_in_claim = create_a_claim(
                                    data_site,
                                    "P1433",
                                    journal_item_page,
                                    item,
                                    item_id,
                                )
                                # add sources to claim
                                article_sources = (
                                    construct_sources_to_article_claim(
                                        data_site, bibcode
                                    )
                                )
                                add_sources_to_claim(
                                    article_sources, published_in_claim
                                )
                    elif fl_item_id == "P1476":
                        wb_text = WbMonolingualText(
                            text=strip_html_tags_from_title(value[0]),
                            language="en",
                        )
                        claim = create_a_claim(
                            data_site, fl_item_id, wb_text, item, item_id
                        )
                        if detect_if_title_contains_html_tag(value[0]):
                            wb_text_in_html = WbMonolingualText(
                                text=value[0], language="en"
                            )
                            # add P6833 (title in HTML) qualifier to P1476 (title)
                            add_qualifiers_to_claim(
                                data_site, "P6833", wb_text_in_html, claim
                            )
                        # add sources to claim
                        article_sources = construct_sources_to_article_claim(
                            data_site, bibcode
                        )
                        add_sources_to_claim(article_sources, claim)
                    elif fl_item_id == "P1104":
                        # Q1069725 page item
                        pages_item_page = ItemPage(data_site, "Q1069725")
                        wb_quant = WbQuantity(
                            value,
                            pages_item_page,
                            site=data_site,
                        )
                        claim = create_a_claim(
                            data_site, fl_item_id, wb_quant, item, item_id
                        )
                        # add sources to claim
                        article_sources = construct_sources_to_article_claim(
                            data_site, bibcode
                        )
                        add_sources_to_claim(article_sources, claim)
                    elif fl_item_id == "P577":
                        date_time = parse(value)
                        wb_time = WbTime(
                            year=date_time.year,
                            month=date_time.month,
                            site=data_site,
                        )
                        claim = create_a_claim(
                            data_site, fl_item_id, wb_time, item, item_id
                        )
                        # add sources to claim
                        article_sources = construct_sources_to_article_claim(
                            data_site, bibcode
                        )
                        add_sources_to_claim(article_sources, claim)
                    elif fl_item_id == "P2093":
                        for index, v in enumerate(value):
                            # skip if there are other strings e.g. collaboration
                            # in the author name
                            if name_separator in v:
                                # get author full name
                                author_name = format_author_name(v)
                                # get author first name
                                author_given_names = get_author_given_names(v)
                                # get author family name
                                author_last_names = get_author_last_names(v)

                                # try to look at orcid
                                if (
                                    orcid_pub_list
                                    and orcid_pub_list[index] != empty_value
                                ):
                                    print(author_name, orcid_pub_list[index])

                                    # search if an orcid id exists on wikidata
                                    search_orcid_query = (
                                        search_orcid_id_sparql
                                        % (orcid_pub_list[index])
                                    )
                                    result = sparql_query_wrapper.query(
                                        search_orcid_query
                                    )

                                    # found orcid id on wikidata, add author statement to article
                                    if result["results"]["bindings"]:
                                        print("orcid already exists")
                                        # expect 1 result means there's only one orcid on wikidata
                                        author_item_id = result["results"][
                                            "bindings"
                                        ][0]["item"]["value"].replace(
                                            url_prefix, ""
                                        )
                                        author_item_page = ItemPage(
                                            data_site, author_item_id
                                        )
                                        claim = create_a_claim(
                                            data_site,
                                            "P50",
                                            author_item_page,
                                            item,
                                            item_id,
                                        )
                                        add_qualifiers_to_author_item(
                                            data_site,
                                            index,
                                            affiliation_list,
                                            author_name,
                                            author_given_names,
                                            author_last_names,
                                            claim,
                                        )
                                        # add sources to claim
                                        article_sources = (
                                            construct_sources_to_article_claim(
                                                data_site, bibcode
                                            )
                                        )
                                        add_sources_to_claim(
                                            article_sources, claim
                                        )
                                    # orcid id not found on wikidata, but exists in ADS, create author item and add related orcid to wikidata
                                    else:
                                        # step 1: create author item
                                        author_item = create_wikidata_item_page(
                                            "en",
                                            author_name,
                                            f"researcher, ORCID iD = {orcid_pub_list[index]}",
                                            data_site,
                                        )
                                        author_item_id = author_item.getID()
                                        print(
                                            f"new author item: {url_prefix}{author_item_id}"
                                        )

                                        # add instance of Q5 (human) to author item
                                        human_item_page = ItemPage(
                                            data_site, "Q5"
                                        )
                                        create_a_claim(
                                            data_site,
                                            "P31",
                                            human_item_page,
                                            author_item,
                                            author_item_id,
                                        )

                                        # search with given name item with initials
                                        search_given_name_query = (
                                            search_item_with_instance_given_name_sparql
                                            % (author_given_names)
                                        )
                                        result = sparql_query_wrapper.query(
                                            search_given_name_query
                                        )
                                        if result["results"]["bindings"]:
                                            # add given name string claim to author item
                                            given_name_item = result[
                                                "results"
                                            ]["bindings"][0]["item"][
                                                "value"
                                            ].replace(
                                                url_prefix, ""
                                            )
                                            given_name_item_page = ItemPage(
                                                data_site, given_name_item
                                            )
                                            given_name_claim = create_a_claim(
                                                data_site,
                                                "P735",
                                                given_name_item_page,
                                                author_item,
                                                author_item_id,
                                            )
                                            # add source of given name to author item
                                            author_sources = construct_sources_to_author_claim(
                                                data_site
                                            )
                                            add_sources_to_claim(
                                                author_sources,
                                                given_name_claim,
                                            )

                                        # search with family name item
                                        search_family_name_query = (
                                            search_item_with_instance_family_name_sparql
                                            % (author_last_names)
                                        )
                                        result = sparql_query_wrapper.query(
                                            search_family_name_query
                                        )
                                        if result["results"]["bindings"]:
                                            # add family name claim to author item
                                            family_name_item = result[
                                                "results"
                                            ]["bindings"][0]["item"][
                                                "value"
                                            ].replace(
                                                url_prefix, ""
                                            )
                                            family_name_item_page = ItemPage(
                                                data_site, family_name_item
                                            )
                                            family_name_claim = create_a_claim(
                                                data_site,
                                                "P734",
                                                family_name_item_page,
                                                author_item,
                                                author_item_id,
                                            )
                                            # add source of family name to author item
                                            author_sources = construct_sources_to_author_claim(
                                                data_site
                                            )
                                            add_sources_to_claim(
                                                author_sources,
                                                family_name_claim,
                                            )

                                        # add orcid claim to author item
                                        orcid_claim = create_a_claim(
                                            data_site,
                                            "P496",
                                            orcid_pub_list[index],
                                            author_item,
                                            author_item_id,
                                        )
                                        # add source of orcid to author item
                                        author_sources = (
                                            construct_sources_to_author_claim(
                                                data_site
                                            )
                                        )
                                        add_sources_to_claim(
                                            author_sources, orcid_claim
                                        )

                                        # add occupation associated to orcid, Q1650915 researcher
                                        researcher_item_page = ItemPage(
                                            data_site, "Q1650915"
                                        )
                                        create_a_claim(
                                            data_site,
                                            "P106",
                                            researcher_item_page,
                                            author_item,
                                            author_item_id,
                                        )

                                        # step 2: add author item to article
                                        author_item_page = ItemPage(
                                            data_site, author_item_id
                                        )
                                        claim = create_a_claim(
                                            data_site,
                                            "P50",
                                            author_item_page,
                                            item,
                                            item_id,
                                        )
                                        add_qualifiers_to_author_item(
                                            data_site,
                                            index,
                                            affiliation_list,
                                            author_name,
                                            author_given_names,
                                            author_last_names,
                                            claim,
                                        )
                                        # add sources to claim
                                        article_sources = (
                                            construct_sources_to_article_claim(
                                                data_site, bibcode
                                            )
                                        )
                                        add_sources_to_claim(
                                            article_sources, claim
                                        )
                                # orcid id not found in ADS, add author name string to article
                                else:
                                    claim = create_a_claim(
                                        data_site,
                                        fl_item_id,
                                        author_name,
                                        item,
                                        item_id,
                                    )
                                    add_qualifiers_to_author_string(
                                        data_site,
                                        index,
                                        affiliation_list,
                                        author_given_names,
                                        author_last_names,
                                        claim,
                                    )
                                    # add sources to claim
                                    article_sources = (
                                        construct_sources_to_article_claim(
                                            data_site, bibcode
                                        )
                                    )
                                    add_sources_to_claim(
                                        article_sources, claim
                                    )
                    else:
                        if type(value) is str:
                            claim = create_a_claim(
                                data_site, fl_item_id, value, item, item_id
                            )
                            # add sources to claim
                            article_sources = (
                                construct_sources_to_article_claim(
                                    data_site, bibcode
                                )
                            )
                            add_sources_to_claim(article_sources, claim)
                        else:
                            for v in value:
                                claim = create_a_claim(
                                    data_site,
                                    fl_item_id,
                                    str(v),
                                    item,
                                    item_id,
                                )
                                # add sources to claim
                                article_sources = (
                                    construct_sources_to_article_claim(
                                        data_site, bibcode
                                    )
                                )
                                add_sources_to_claim(article_sources, claim)


# extract arxiv id from arxiv string
def extract_arxiv_digits_from_arxiv_id(arxiv_ids: str) -> str:
    # split to lists
    digits_lists = arxiv_ids.split(arxiv_identifier)
    # get the second list
    arxiv_id = digits_lists[1]
    # remove the last character
    arxiv_id_digits = arxiv_id[:-1]
    if "." not in arxiv_id_digits:
        # it's 5 digits string
        # joining string at position 4
        new_arxiv_id_digits = "{0}.{1}".format(
            arxiv_id_digits[:4], arxiv_id_digits[4:]
        )
        return new_arxiv_id_digits
    else:
        return arxiv_id_digits


# filter arXiv ids from bibcodes
def filter_arxiv_ids_from_alternate_bibcodes(bibcodes):
    return list(filter(lambda bibcode: arxiv_identifier in bibcode, bibcodes))


# add qualifiers to author string
def add_qualifiers_to_author_string(
    data_site,
    index,
    affiliation_lists,
    author_given_names,
    author_last_names,
    claim,
):
    # add serials ordinal P1545
    add_qualifiers_to_claim(data_site, "P1545", str(index + 1), claim)
    # add author given names P9687
    add_qualifiers_to_claim(data_site, "P9687", author_given_names, claim)
    # add author last names P9688
    add_qualifiers_to_claim(data_site, "P9688", author_last_names, claim)
    # add affiliation P6424 to author if it's not empty
    if affiliation_lists and affiliation_lists[index] != empty_value:
        affiliation = affiliation_lists[index]
        if affiliation_separator in affiliation:
            # split affiliation to list
            affiliation_list_of_author = affiliation.split(
                affiliation_separator
            )
            for affiliations in affiliation_list_of_author:
                # strip the string
                striped_affiliations = affiliations.strip()
                # add affiliation to author
                add_qualifiers_to_claim(
                    data_site, "P6424", striped_affiliations, claim
                )
        else:
            # strip the string
            striped_affiliation = affiliation.strip()
            # add affiliation to author
            add_qualifiers_to_claim(
                data_site, "P6424", striped_affiliation, claim
            )


# add qualifiers to author item
def add_qualifiers_to_author_item(
    data_site,
    index,
    affiliation_lists,
    author_name,
    author_given_names,
    author_last_names,
    claim,
):
    add_qualifiers_to_author_string(
        data_site,
        index,
        affiliation_lists,
        author_given_names,
        author_last_names,
        claim,
    )
    # add object stated as (P1932) from source of name in ADS database
    add_qualifiers_to_claim(data_site, "P1932", author_name, claim)


# construct a claim
def construct_a_claim(data_site, prop, target) -> Claim:
    claim = Claim(data_site, prop)
    claim.setTarget(target)
    return claim


# create a claim for a given item
def create_a_claim(data_site, fl_item_id, target, item, item_id) -> Claim:
    claim = construct_a_claim(data_site, fl_item_id, target)
    print(f"claim: {claim}")
    item.addClaim(
        claim,
        summary=f"Adding claim {fl_item_id} to {item_id}",
    )
    return claim


# add qualifiers to a given claim
def add_qualifiers_to_claim(data_site, qualifier_id, target, claim):
    qualifier = construct_a_claim(data_site, qualifier_id, target)
    print(f"qualifier: {qualifier}")
    claim.addQualifier(
        qualifier, summary=f"Adding a qualifier {qualifier_id}."
    )


# add sources to a given claim
def add_sources_to_claim(sources, claim):
    print(f"sources: {sources}")
    # add sources to a claim
    claim.addSources(sources, summary=f"Adding sources to claim.")


# construct stated in (P248) and retrieved (P813) to author claim
def construct_sources_to_author_claim(data_site) -> list:
    # stated in (P248)
    target = ItemPage(data_site, "Q752099")  # ADS item
    stated_in = construct_a_claim(data_site, "P248", target)

    # retrieved (P813). Data type: Point in time
    today = date.today()  # Date today
    date_created = WbTime(
        year=int(today.strftime("%Y")),
        month=int(today.strftime("%m")),
        day=int(today.strftime("%d")),
    )  # retrieved -> %DATE TODAY%.
    retrieved = construct_a_claim(data_site, "P813", date_created)

    author_claim_sources = [stated_in, retrieved]
    return author_claim_sources


# construct stated in (P248), retrieved (P813) and ADS bibcode (P819) to article claim
def construct_sources_to_article_claim(data_site, bibcode) -> list:
    author_claim_sources: list = construct_sources_to_author_claim(data_site)
    # ADS bibcode (P819)
    ads_bibcode = construct_a_claim(data_site, "P819", bibcode)
    # join ADS bibcode with author claim sources to form article claim sources
    article_claim_sources = author_claim_sources + [ads_bibcode]
    return article_claim_sources


def create_wikidata_item_page(
    lang: str, title: str, description: str, data_site: DataSite
) -> ItemPage:
    wikidata_item = WikidataItem(data_site, {lang: title}, {lang: description})
    new_item_page = wikidata_item.create_item_page()
    return new_item_page


def get_author_given_names(author) -> str:
    # split author first and last name
    names = split_author_name(author)
    # get author first names
    author_given_names = names[1]
    return author_given_names


def get_author_last_names(author) -> str:
    # split author first and last name
    names = split_author_name(author)
    # get author last name
    author_last_names = names[0]
    return author_last_names


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


if __name__ == "__main__":  # pragma: no cover
    import_from_ads(
        "../../sparql/wikidata/queries/query_surname_in_english.sparql",
        "r",
        "https://raw.githubusercontent.com/adsabs/adsabs-dev-api/master/openapi/parameters.yaml",
        "../../sparql/wikidata/queries/query_list_of_solr_fields_on_ads.sparql",
        "../surname/wikidata_key_replace_map.json",
        "../../sparql/wikidata/queries/search_if_a_doi_exists.sparql",
        "../../sparql/wikidata/queries/search_an_item_with_instance_of_family_name.sparql",
        "../../sparql/wikidata/queries/search_an_item_with_instance_of_given_name.sparql",
        "../../sparql/wikidata/queries/search_if_an_orcid_id_exists.sparql",
        "../../sparql/wikidata/queries/search_if_ads_bibcode_exists.sparql",
        "../../sparql/wikidata/queries/search_if_an_issn_exists.sparql",
    )
