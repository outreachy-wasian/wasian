#!/usr/local/bin/python3
from pywikibot.data.sparql import SparqlQuery
import codecs

outputfile = codecs.open('populate_family_names_cache.csv', "w", "utf-8")

surname_query = open("../../sparql/wikidata/queries/surname.sparql", "r").read()
sq = SparqlQuery()
queryresult = sq.query(surname_query)
for resultitem in queryresult['results']['bindings']:
    print(resultitem['item']['value'].replace('http://www.wikidata.org/entity/','') + ', ' + resultitem['itemLabel']['value'])
    outputfile.write(resultitem['item']['value'].replace('http://www.wikidata.org/entity/','') + ',' + resultitem['itemLabel']['value']+"\n")

outputfile.close()
print('Done!')
