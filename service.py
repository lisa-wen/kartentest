import tantivy
from tantivy import Query, Occur
import json
import pickle
from annoy import AnnoyIndex

json_field_list = ["id", "tags", "types", "resources", "origins", "license", "organisations", "time_ranges",
                   "quality"]
# Declaring our schema.
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("source", stored=True)
schema_builder.add_text_field("id", stored=True)
schema_builder.add_text_field("source_url", stored=True)
schema_builder.add_text_field("title", stored=True, tokenizer_name='de_stem')
schema_builder.add_text_field("description", stored=True, tokenizer_name='de_stem')
schema_builder.add_text_field("umthes", stored=True)
schema_builder.add_text_field("bounding_boxes", stored=True)
schema_builder.add_text_field("data_types", stored=True)
schema_builder.add_text_field("portals", stored=True)
schema_builder.add_text_field("files", stored=True)
schema_builder.add_text_field("fair", stored=True)
for field in json_field_list:
    schema_builder.add_json_field(field + '_json', stored=True)
schema = schema_builder.build()

index_path = "index_path"
index = tantivy.Index(schema, path=str(index_path))
searcher = index.searcher()

# Needed for annoy index and recommendations
TOPN_DEFAULT = 10

embedding_dim = 768
embedding_index = AnnoyIndex(embedding_dim, 'euclidean')
embedding_index.load('embeddings.ann')

with open('title.pkl', 'rb') as data_file:
    titles = pickle.load(data_file)

keys = titles.keys()
values = titles.values()
ids = [k for k in keys]
title_list = [list(v)[0] for v in values]
num_items = len(titles)


def search(query: str, topn: int, field_names=None):
    if field_names is None:
        field_names = ["title", "description"]
    query = index.parse_query(query, field_names)
    results = searcher.search(query, topn)
    return results


def search_by_id(id):
    try:
        query = index.parse_query(f'id:{id}')
    except (ValueError, SyntaxError) as e:
        query = index.parse_query(f'id:_{id}')
    results = searcher.search(query, 1)
    (score, address) = results.hits[0]
    doc = searcher.doc(address)
    return doc


def get_doc(address):
    return searcher.doc(address)


def process_doc(doc):
    item_data = {
        "id": doc['id'][0],
        "title": doc['title'][0],
    }
    umthes_list = [tag['Umthes'] for tag in json.loads(doc['umthes'][0]) if 'Umthes' in tag]
    item_data['umthes'] = umthes_list
    if doc['bounding_boxes']:
        item_data['bounding_boxes'] = json.loads(doc['bounding_boxes'][0])
    item_data['source_url'] = doc['source_url'][0]
    item_data['description'] = doc['description'][0]
    return item_data


def process_mlt_results(results, top, input_id):
    final_results = []
    for (score, address) in results.hits:
        if len(final_results) < top:
            doc = searcher.doc(address)
            if input_id != doc['id'][0]:
                item_data = process_doc(doc)
                final_results.append(item_data)
    return final_results


def embedding(id: str, topn: int) -> dict:
    title_idx = list(keys).index(id)
    if topn is None:
        recommendations = embedding_index.get_nns_by_item(title_idx, TOPN_DEFAULT)
    else:
        recommendations = embedding_index.get_nns_by_item(title_idx, topn)
    recommendations_list = []
    for recommendation in recommendations:
        if recommendation != title_idx:
            try:
                doc = search_by_id(ids[recommendation])
                item_data = process_doc(doc)
                recommendations_list.append(item_data)
            except Exception as e:
                print("Could not process recommendation:", e)
    return recommendations_list


def more_like_this(address, top):
    queries = []
    this = searcher.doc(address)
    umthes_list = [tag['Umthes'] for tag in json.loads(this['umthes'][0]) if 'Umthes' in tag]
    for tag in umthes_list:
        mlt_query = index.parse_query(tag['label'], ['umthes'])
        queries.append((Occur.Should, mlt_query))
    boolean_query = Query.boolean_query(queries)
    results = searcher.search(boolean_query, limit=top)
    return process_mlt_results(results, top, this['id'][0])

