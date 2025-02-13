# References:
# https://lucene.apache.org/pylucene/
# https://lucene.apache.org/core/6_2_0/core/overview-summary.html
# https://svn.apache.org/viewvc/lucene/pylucene/trunk/samples/IndexFiles.py?view=markup
# https://www.youtube.com/watch?v=kTdfhmpPDG8

import os
import json
import time
import lucene
from org.apache.lucene.store import SimpleFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.en import EnglishAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField, IntPoint, StoredField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.search.similarities import BM25Similarity

# Import the database 
data_path = './test_dataset/'

dataset = []
# Load all Json files under the directory
# Right now we will only save the following attributes: [title, id, score, permalink, body]
for file_name in os.listdir(data_path):
    if file_name.endswith(".json"):
        with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as file:
            # Load data
            reddits = json.load(file)
            # Extract attribute
            for reddit in reddits:
                curr_reddit = {
                    'title': reddit.get("title", ""),
                    'id': reddit.get("id", ""),
                    'score': str(reddit.get("score", "")),
                    'permalink': reddit.get("permalink", ""),
                    'body': reddit.get("body", "")
                }
                dataset.append(curr_reddit)
print(f"Successfully retrieved {len(dataset)} Reddit posts.")

def create_index(dir):
    # Define the dir where indexes will be stored
    if not os.path.exists(dir):
        os.mkdir(dir)
    store = SimpleFSDirectory(Paths.get(dir))

    # Standard Setup
    # Standard Analyzer only includes tokenization while EnglishAnalyzer handles stopwords and stemming
    # analyzer = StandardAnalyzer()
    analyzer = EnglishAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    # By default, Pylucene uses Tf-IDF, we can switch it to BM25
    # config.setSimilarity(BM25Similarity())
    writer = IndexWriter(store, config)

    # Metadata field, ex: title
    metaType = FieldType()
    metaType.setStored(True)
    metaType.setTokenized(False)
    metaType.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    # Context field, body text
    # Need tokenization
    contextType = FieldType()
    contextType.setStored(True)
    contextType.setTokenized(True)
    contextType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    # Retrieve document by document from the stored array
    for reddit in dataset:
        title = reddit['title']
        id = reddit['id']
        score = reddit['score']
        permalink = reddit['permalink']
        body = reddit['body']

        doc = Document()
        # StringField is better for exact matching (ID and permalink)
        doc.add(Field('Title', str(title), metaType))
        doc.add(Field('ID', str(id), StringField.TYPE_STORED))
        # Score need to be a number that can be queried by range
        # https://lucene.apache.org/core/6_2_0/core/org/apache/lucene/document/IntPoint.html
        # Index for range filter
        doc.add(IntPoint("Score", int(score)))
        # Store the score value
        doc.add(StoredField("Score", int(score)))
        doc.add(Field('Permalink', str(permalink), StringField.TYPE_STORED))
        doc.add(Field('Body', str(body), contextType))
        writer.addDocument(doc)
    writer.close()

lucene.initVM(vmargs=['-Djava.awt.headless=true'])
# Add time function to measure indexing time
start_time = time.time()
create_index('lucene_index/')
end_time = time.time()
index_time = end_time - start_time
print(f"Indexing completed in {index_time} seconds.")

# query_terms = "UC Riverside"
# retrieve('lucene_index/', query_terms)