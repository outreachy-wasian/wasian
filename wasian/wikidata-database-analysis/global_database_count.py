import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api
from pywikibot.data.sparql import SparqlQuery

# connect to wikidata
wd_connect = pywikibot.Site("wikidata", "wikidata")
wd = wd_connect.data_repository()
# dictionary with all scholarly databases
sch_p = {}

# gets all scholarly databases and sets them as keys in dictionary
# these are items where P31 (Instance of) = Q29548341 (Wikidata property for items about scholarly articles)
def get_scholarly_databases():
    with open("scholarly_query.rq", "r") as s_file:
        s = s_file.read()
        s = s[0:-1]
    generator = pagegenerators.WikidataSPARQLPageGenerator(s, site=wd)
    # add each database property to dictionary
    for page in generator:
        sch_p[page.title()[9:]] = 0
    # remove DOI as not relevant
    sch_p.pop("P356")
    # PubMed ID added manually due to timing out in SPARQL.
    # Sourced from: https://www.wikidata.org/wiki/Special:MostLinkedPages
    sch_p["P698"] = "17803970"


# get number of articles that have database as an identifier.
def get_article_count(database):
    s = (
        "SELECT (COUNT (DISTINCT ?item) AS ?count) WHERE { ?item wdt:"
        + database
        + "?value }"
    )
    sq = SparqlQuery()
    count = sq.query(s)
    sch_p[database] = count["results"]["bindings"][0]["count"]["value"]


# convert dictionary to CSV file
def write_data(databases):
    with open("data/total_database_count.csv", "w") as f:
        print("Writing global database count...")
        f.write("Database,Count\n")
        for database in sch_p:
            db_count = sch_p[database]
            f.write(database + "," + str(db_count) + "\n")
        f.close()


# begin by setting up database dictionary
get_scholarly_databases()

# for each item in database (except pubmed ID) get count through sparql
for database in set(sch_p) - {"P698"}:
    print("Getting article count for database: " + database)
    get_article_count(database)

write_data(sch_p)
