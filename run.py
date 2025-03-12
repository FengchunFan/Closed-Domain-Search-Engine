#file modified based on the sample provided by Mr.SHIHAB RASHID from CS172 in UC riverside
#export FLASK_APP=run
#flask run -h 0.0.0.0 -p 8888 --debug
#http://169.235.31.51:8888

import logging, sys
logging.disable(sys.maxsize)

import lucene
import os
import csv
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions, DirectoryReader
from org.apache.lucene.search import IndexSearcher, BoostQuery, Query, BooleanQuery, BooleanClause
from org.apache.lucene.search.similarities import BM25Similarity
from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__) #instance of flask class
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

#import the database 
for i in range(51):
    data_path = f'./data/output{i}.csv'
    sample_doc = []
    with open(data_path, 'r', encoding='utf-8', errors='replace') as file:
        reader = csv.reader(file)
        for row in reader:
            title = row[0]
            context = row[1]
            url = row[2]
            temp_doc = {
                'title' : title,
                'context' : context,
                'url' : url
            }
            sample_doc.append(temp_doc)

def create_index(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
    store = SimpleFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)

    contextType = FieldType()
    contextType.setStored(True)
    contextType.setTokenized(True)
    contextType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    #retrieve document by document from the stored array
    for sample in sample_doc:
        title = sample['title']
        context = sample['context']
        url = sample['url']

        doc = Document()
        doc.add(Field('Title', str(title), metaType))
        doc.add(Field('Context', str(context), contextType))
        doc.add(Field('Url', str(url), StringField.TYPE_STORED))
        writer.addDocument(doc)
    writer.close()

#for query, count in both title and context and add more score if query appear in title
def retrieve(storedir, query, add_info):
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    
    parser_title = QueryParser('Title', StandardAnalyzer())
    parsed_query_title = parser_title.parse(query)
    parser_context = QueryParser('Context', StandardAnalyzer())
    parsed_query_context = parser_context.parse(query)

    #boost score if query appear in title
    boosted_query_title = BoostQuery(parsed_query_title, 2.0)

    #consulted chatgpt on combining weight of two fields
    boolean_query = BooleanQuery.Builder()
    boolean_query.add(boosted_query_title, BooleanClause.Occur.SHOULD)
    boolean_query.add(parsed_query_context, BooleanClause.Occur.SHOULD)

    #give more weiht to additional info
    if(add_info != ""):
        parser_title_a = QueryParser('Title', StandardAnalyzer())
        parsed_info_title_a = parser_title_a.parse(add_info)
        parser_context_a = QueryParser('Context', StandardAnalyzer())
        parsed_info_context_a = parser_context_a.parse(add_info) 

        boosted_info_title_a = BoostQuery(parsed_info_title_a, 2.0)
        boosted_info_context_a = BoostQuery(parsed_info_context_a, 2.5)    
        boolean_query.add(boosted_info_title_a, BooleanClause.Occur.SHOULD)
        boolean_query.add(boosted_info_context_a, BooleanClause.Occur.SHOULD)    

    topDocs = searcher.search(boolean_query.build(), 10).scoreDocs
    with open("./static/result.csv", mode='a', newline='') as file:
        file.truncate(0)
        file.close()
    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        data_title = doc.get("Title")
        data_text = " " + doc.get("Context")
        data_url = doc.get("Url")
        score = hit.score
        data = [data_title, data_text, data_url, score]
        with open("./static/result.csv", mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([str(item).replace('\n', '') for item in data])
                file.close()

create_index('lucene_index/')

@app.route('/', methods = ['POST', 'GET'])
def input():
    return render_template('input.html')

@app.route('/output', methods = ['POST', 'GET'])
def output():
    if request.method == 'GET':
        return f"Nothing"
    if request.method == 'POST':
        form_data = request.form
        query = form_data['query']
        print(f"this is the query: {query}")
        add_info = form_data['add_info']
        print(f"this is the additional info: {add_info}")
        lucene.getVMEnv().attachCurrentThread()
        retrieve('lucene_index/', str(query))
        return render_template('output.html')

@app.route("/result.csv")
def retrieve_result():
    return send_from_directory("static", "result.csv")

if __name__ == "__main__":
    app.run(debug=True)