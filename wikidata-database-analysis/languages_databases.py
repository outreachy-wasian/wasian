import pywikibot
from pywikibot.data import api
from pywikibot import pagegenerators

# connect to wikidata
wd_connect = pywikibot.Site('wikidata', 'wikidata')
wd = wd_connect.data_repository()

#chinese, spanish, portugese, russian, japanese, french, korean, german, italian, dutch
language_list = ['Q7850', 'Q1321', 'Q5146', 'Q7737', 'Q5287', 'Q150', 'Q9176', 'Q188', 'Q652', 'Q7411']

#dictionary with all scholarly databases
sch_p = {}

#gets all scholarly databases and sets them as keys in dictionary
#these are items where P31 (Instance of) = Q29548341 (Wikidata property for items about scholarly articles)
def get_scholarly_databases():
    with open('scholarly_query.rq', 'r') as s_file:
        s = s_file.read()
        s = s[0:-1]
    generator = pagegenerators.WikidataSPARQLPageGenerator(s, site=wd)
    #add each database property to dictionary
    for page in generator:
        sch_p[page.title()[9:]] = 0
    #remove DOI as not relevant 
    sch_p.pop('P356')

#get sample of 2000 scholarly articles for given language
def get_scholarly_articles(language):
    s = 'SELECT ?item WHERE { ?item wdt:P31 wd:Q13442814; wdt:P407 wd:' + language + '.} LIMIT 2000'
    generator = pagegenerators.WikidataSPARQLPageGenerator(s, site=wd)
    i = 0
    for page in generator:
        i += 1
        print(i)
        #for each scholarly article in sample, get count of each scholarly article
        get_database_count(page)

#given a scholarly article, add to database count in dictionary if in article
def get_database_count(page):
    wd_info = page.get()
    for database in sch_p:
        if database in wd_info['claims']:
            sch_p[database] += 1

#convert dictionary to CSV file for each language
def write_data(language):
    with open('data/' + language + '_database_count.csv', 'w') as f:
        print('Writing ' + language + ' database count...')
        f.write('Database,Count\n')
        for database in sch_p:
            db_count = sch_p[database]
            f.write(database + ',' + str(db_count) + '\n')
        f.close()

#begin by setting up database dictionary
get_scholarly_databases()
#get database count for each language, resetting dictionary at each turn
for language in language_list:
    print('Getting ' + language + ' database count!')
    get_scholarly_articles(language)
    write_data(language)
    sch_p = dict.fromkeys(sch_p, 0)
