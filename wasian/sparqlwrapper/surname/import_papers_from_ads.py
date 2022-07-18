#!/usr/local/bin/python3
import sys
from json import loads
from typing import Dict, List

from ads import SearchQuery
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

orcid_pub_list = []
url_prefix = "http://www.wikidata.org/entity/"
name_separator = ", "


# Using surnames from Wikidata as key to search articles in ADS database, import scholarly articles and create Wikidata items.
def import_from_ads(
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
    global orcid_pub_list

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

        # For test
        # search_query: SearchQuery = SearchQuery(bibcode="1953Natur.171..737W", fl=search_field)

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
                if (
                    result["results"]["bindings"][0]["boolean"]["value"]
                    == "true"
                ):
                    print(f"{doi} already exists, don't do anything")
                else:
                    print(f"{doi} does not exist on wikidata, creating item")
                    # get title of article
                    title = article.title[0]
                    # get date of article
                    date = article.date
                    # process title and description
                    striped_title = strip_html_tags_from_title(title)
                    print(striped_title)
                    description = compose_description_from_date(date)
                    print(description)
                    # create Wikidata item
                    item = create_wikidata_item_page(
                        "en", striped_title, description, data_site
                    )
                    item_id = item.getID()
                    print(item_id)
                    search_and_add_statement_from_ads(
                        item_id,
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
            # if doi isn't available in ADS, search title in ADS
            else:
                print("title: ", article.title)
                title: str = article.title[0]
                search_title_query = search_item_sparql % (title)
                result = sparql_query_wrapper.query(search_title_query)
                if result["results"]["bindings"]:
                    print(f"{title} already exists, don't do anything")
                else:
                    print(f"{title} does not exist on wikidata, creating item")
                    # get title of article
                    title = article.title[0]
                    # get date of article
                    date = article.date
                    # process title and description
                    striped_title = strip_html_tags_from_title(title)
                    print(striped_title)
                    description = compose_description_from_date(date)
                    print(description)
                    item = create_wikidata_item_page(
                        "en", striped_title, description, data_site
                    )
                    item_id = item.getID()
                    print(item_id)
                    search_and_add_statement_from_ads(
                        item_id,
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


# TODO: save raw HTML as string to P6833 (title in HTML) under title before stripping
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


# Automatically search and add statements from ADS
def search_and_add_statement_from_ads(
    item_id: str,
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
                    item = ItemPage(data_site, item_id)

                    # Manually add P31 (instance of) statement to wikidata item
                    # Q13442814 is scholarly article id
                    scholarly_article_page = ItemPage(data_site, "Q13442814")
                    create_a_claim(
                        data_site, "P31", scholarly_article_page, item, item_id
                    )

                    if fl_item_id == "P1476":
                        wb_text = WbMonolingualText(text=value, language="en")
                        create_a_claim(
                            data_site, fl_item_id, wb_text, item, item_id
                        )
                    elif fl_item_id == "P1104":
                        # Q1069725 page
                        pages_item_page = ItemPage(data_site, "Q1069725")
                        wb_quant = WbQuantity(
                            value,
                            pages_item_page,
                            site=data_site,
                        )
                        create_a_claim(
                            data_site, fl_item_id, wb_quant, item, item_id
                        )
                    elif fl_item_id == "P577":
                        date_time = parse(value)
                        wb_time = WbTime(
                            year=date_time.year,
                            month=date_time.month,
                            site=data_site,
                        )
                        create_a_claim(
                            data_site, fl_item_id, wb_time, item, item_id
                        )
                    elif fl_item_id == "P2093":
                        for index, v in enumerate(value):
                            # skip if there are other strings e.g. collaboration
                            # in the author name
                            if name_separator in v:
                                # get author name
                                author_name = format_author_name(v)
                                # try to look at orcid
                                if orcid_pub_list[index] != "-":
                                    print(author_name, orcid_pub_list[index])

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
                                        author_item_page = ItemPage(
                                            data_site, author_item_id
                                        )
                                        create_a_claim(
                                            data_site,
                                            "P50",
                                            author_item_page,
                                            item,
                                            item_id,
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
                                        print(author_item_id)

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

                                        # split author name into first and last name
                                        author_name_split = split_author_name(
                                            v
                                        )
                                        print(author_name_split)

                                        # search with given name item with initials
                                        search_given_name_query = (
                                            search_item_with_instance_given_name_sparql
                                            % (author_name_split[1])
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
                                            create_a_claim(
                                                data_site,
                                                "P735",
                                                given_name_item_page,
                                                author_item,
                                                author_item_id,
                                            )

                                        # search with family name item
                                        search_family_name_query = (
                                            search_item_with_instance_family_name_sparql
                                            % (author_name_split[0])
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
                                            create_a_claim(
                                                data_site,
                                                "P734",
                                                family_name_item_page,
                                                author_item,
                                                author_item_id,
                                            )

                                        # add orcid claim to author item
                                        create_a_claim(
                                            data_site,
                                            "P496",
                                            orcid_pub_list[index],
                                            author_item,
                                            author_item_id,
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
                                        create_a_claim(
                                            data_site,
                                            "P50",
                                            author_item_page,
                                            item,
                                            item_id,
                                        )
                                # orcid id not found in ADS, add author name string to article
                                else:
                                    create_a_claim(
                                        data_site,
                                        fl_item_id,
                                        author_name,
                                        item,
                                        item_id,
                                    )
                    else:
                        if type(value) is str:
                            try:
                                create_a_claim(
                                    data_site, fl_item_id, value, item, item_id
                                )
                            # it's a publication
                            except:
                                publication_query = (
                                    search_publication_sparql % (value)
                                )
                                result = sparql_query_wrapper.query(
                                    publication_query
                                )
                                if result["results"]["bindings"]:
                                    qid = result["results"]["bindings"][0][
                                        "item"
                                    ]["value"].replace(url_prefix, "")
                                    print(qid)
                                    publication_item_page = ItemPage(
                                        data_site, qid
                                    )
                                    create_a_claim(
                                        data_site,
                                        fl_item_id,
                                        publication_item_page,
                                        item,
                                        item_id,
                                    )
                                else:
                                    print(f"{value} not found")
                        else:
                            for v in value:
                                create_a_claim(
                                    data_site,
                                    fl_item_id,
                                    str(v),
                                    item,
                                    item_id,
                                )


# create a claim for a given item
def create_a_claim(data_site, fl_item_id, target, item, item_id):
    claim = Claim(data_site, fl_item_id)
    claim.setTarget(target)
    print(claim)
    item.addClaim(
        claim,
        summary=f"Adding claim {fl_item_id} to {item_id}",
    )


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


def add_affiliation_to_author_item(author_item_id, affiliation, item_id):
    wikidata_site = WikidataSite("wikidata", "wikidata")
    data_site = wikidata_site.get_data_site()
    item = ItemPage(data_site, author_item_id)
    claim = Claim(data_site, "P2093")
    claim.setTarget(affiliation)
    item.addClaim(claim, summary=f'Adding claim "P2093" to {item_id}')


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
        "../../sparql/wikidata/queries/surname.sparql",
        "r",
        "https://raw.githubusercontent.com/adsabs/adsabs-dev-api/master/openapi/parameters.yaml",
        "../../sparql/wikidata/queries/list_of_solr_fields_on_ads.sparql",
        "../surname/wikidata_key_replace_map.json",
        "../../sparql/wikidata/queries/search_if_an_item_exists.sparql",
        "../../sparql/wikidata/queries/search_if_a_doi_exists.sparql",
        "../../sparql/wikidata/queries/search_an_item_with_instance_of_family_name.sparql",
        "../../sparql/wikidata/queries/search_an_item_with_instance_of_given_name.sparql",
        "../../sparql/wikidata/queries/search_if_a_publication_exists.sparql",
        "../../sparql/wikidata/queries/search_if_an_orcid_id_exists.sparql",
    )
