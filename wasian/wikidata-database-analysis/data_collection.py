import seaborn as sns
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

#convert all language data to pandas dataframe
chinese_data = pd.read_csv('data/Q7850_database_count.csv')
chinese_data = chinese_data[chinese_data.Count != 0]
chinese_data = chinese_data.sort_values(by=['Count'])

spanish_data = pd.read_csv('data/Q1321_database_count.csv')
spanish_data = spanish_data[spanish_data.Count != 0]
spanish_data = spanish_data.sort_values(by=['Count'])

portuguese_data = pd.read_csv('data/Q5146_database_count.csv')
portuguese_data = portuguese_data[portuguese_data.Count != 0]
portuguese_data = portuguese_data.sort_values(by=['Count'])

russian_data = pd.read_csv('data/Q7737_database_count.csv')
russian_data = russian_data[russian_data.Count != 0]
russian_data = russian_data.sort_values(by=['Count'])

japanese_data = pd.read_csv('data/Q5287_database_count.csv')
japanese_data = japanese_data[japanese_data.Count != 0]
japanese_data = japanese_data.sort_values(by=['Count'])

french_data = pd.read_csv('data/Q150_database_count.csv')
french_data = french_data[french_data.Count != 0]
french_data = french_data.sort_values(by=['Count'])

korean_data = pd.read_csv('data/Q9176_database_count.csv')
korean_data = korean_data[korean_data.Count != 0]
korean_data = korean_data.sort_values(by=['Count'])

german_data = pd.read_csv('data/Q188_database_count.csv')
german_data = german_data[german_data.Count != 0]
german_data = german_data.sort_values(by=['Count'])

italian_data = pd.read_csv('data/Q652_database_count.csv')
italian_data = italian_data[italian_data.Count != 0]
italian_data = italian_data.sort_values(by=['Count'])

dutch_data = pd.read_csv('data/Q7411_database_count.csv')
dutch_data = dutch_data[dutch_data.Count != 0]
dutch_data = dutch_data.sort_values(by=['Count'])

global_data = pd.read_csv('data/total_database_count.csv')
global_data = global_data.sort_values(by=['Count'])

mako = sns.color_palette("rainbow", 18)
sns.set_palette(mako)

#create chinese graph
plt.figure(figsize=(10,6))
chinese_graph = sns.barplot(data=chinese_data,x="Database",y="Count")
chinese_graph.set_xticklabels(chinese_graph.get_xticklabels())
chinese_graph.bar_label(chinese_graph.containers[0])
chinese_graph.set_title('Most Linked Academic Databases in Chinese Academic Articles on Wikidata')
plt.savefig("graphs/chinese.png")

#create spanish graph
plt.figure(figsize=(10,6))
spanish_graph = sns.barplot(data=spanish_data,x="Database",y="Count")
spanish_graph.set_xticklabels(spanish_graph.get_xticklabels())
spanish_graph.bar_label(spanish_graph.containers[0])
spanish_graph.set_title('Most Linked Academic Databases in Spanish Academic Articles on Wikidata')
plt.savefig("graphs/spanish.png")

#create portuguese graph
plt.figure(figsize=(10,6))
portuguese_graph = sns.barplot(data=portuguese_data,x="Database",y="Count")
portuguese_graph.set_xticklabels(portuguese_graph.get_xticklabels())
portuguese_graph.bar_label(portuguese_graph.containers[0])
portuguese_graph.set_title('Most Linked Academic Databases in Portuguese Academic Articles on Wikidata')
plt.savefig("graphs/portuguese.png")

#create russian graph
plt.figure(figsize=(10,6))
russian_graph = sns.barplot(data=russian_data,x="Database",y="Count")
russian_graph.set_xticklabels(russian_graph.get_xticklabels())
russian_graph.bar_label(russian_graph.containers[0])
russian_graph.set_title('Most Linked Academic Databases in Russian Academic Articles on Wikidata')
plt.savefig("graphs/russian.png")

#create japanese graph
plt.figure(figsize=(10,6))
japanese_graph = sns.barplot(data=japanese_data,x="Database",y="Count")
japanese_graph.set_xticklabels(japanese_graph.get_xticklabels())
japanese_graph.bar_label(japanese_graph.containers[0])
japanese_graph.set_title('Most Linked Academic Databases in Japanese Academic Articles on Wikidata')
plt.savefig("graphs/japanese.png")

#create french graph
plt.figure(figsize=(10,6))
french_graph = sns.barplot(data=french_data,x="Database",y="Count")
french_graph.set_xticklabels(french_graph.get_xticklabels())
french_graph.bar_label(french_graph.containers[0])
french_graph.set_title('Most Linked Academic Databases in French Academic Articles on Wikidata')
plt.savefig("graphs/french.png")

#create korean graph
plt.figure(figsize=(10,6))
korean_graph = sns.barplot(data=korean_data,x="Database",y="Count")
korean_graph.set_xticklabels(korean_graph.get_xticklabels())
korean_graph.bar_label(korean_graph.containers[0])
korean_graph.set_title('Most Linked Academic Databases in Korean Academic Articles on Wikidata')
plt.savefig("graphs/korean.png")

#create german graph
plt.figure(figsize=(10,5))
german_graph = sns.barplot(data=german_data,x="Database",y="Count")
german_graph.set_xticklabels(german_graph.get_xticklabels())
german_graph.bar_label(german_graph.containers[0])
german_graph.set_title('Most Linked Academic Databases in German Academic Articles on Wikidata')
plt.savefig("graphs/german.png")

#create italian graph
plt.figure(figsize=(10,5))
italian_graph = sns.barplot(data=italian_data,x="Database",y="Count")
italian_graph.set_xticklabels(italian_graph.get_xticklabels())
italian_graph.bar_label(italian_graph.containers[0])
italian_graph.set_title('Most Linked Academic Databases in Italian Academic Articles on Wikidata')
plt.savefig("graphs/italian.png")

#create dutch graph
plt.figure(figsize=(10,6))
dutch_graph = sns.barplot(data=dutch_data,x="Database",y="Count")
dutch_graph.set_xticklabels(dutch_graph.get_xticklabels())
dutch_graph.bar_label(dutch_graph.containers[0])
dutch_graph.set_title('Most Linked Academic Databases in Dutch Academic Articles on Wikidata')
plt.savefig("graphs/dutch.png")

#create global graph: top 15
mako = sns.color_palette("mako", 15)
sns.set_palette(mako)
plt.figure(figsize=(12,12))
global_data_15 = global_data.drop(index=global_data.index[:55])
global_graph_15 = sns.barplot(data=global_data_15,x="Database",y="Count")
global_graph_15.set_xticklabels(global_graph_15.get_xticklabels(), rotation = 45)
global_graph_15.bar_label(global_graph_15.containers[0])
global_graph_15.set_title('15 Most Linked Academic Databases on Wikidata')
plt.savefig("graphs/global_top15.png")

#create global graph: all after top 15 for clarity
mako = sns.color_palette("mako", 55)
sns.set_palette(mako)
plt.figure(figsize=(15,15))
global_data_55 = global_data.drop(index=global_data.index[55:])
global_graph_55 = sns.barplot(data=global_data_55,x="Database",y="Count")
global_graph_55.set_xticklabels(global_graph_55.get_xticklabels(), rotation = 60)
global_graph_55.bar_label(global_graph_55.containers[0], rotation = 90)
global_graph_55.set_title('55 Least Linked Academic Databases on Wikidata')
plt.savefig("graphs/global_bottom55.png")

