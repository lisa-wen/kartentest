import streamlit as st
import toml
import utils as ut
import os
import karten_test
from service import search, get_doc
import json
import tantivy
st.set_page_config(
    page_title="Empfehlungsstudie",
    page_icon="🔎"
)
# Load the TOML configuration
config = toml.load('.streamlit/config.toml')
primary_color = config['theme']['primaryColor']
primary_button = config['theme']['primaryButton']
secondary_button = config['theme']['secondaryButton']

states = ['recommendations', 'recommendations2', 'dataset', 'slider_val', 'checkbox_val'
          'map_recommendations', 'id', 'datasets', 'list1', 'list2', 'state', 'feature_group']

for state in states:
    if state not in st.session_state:
        st.session_state[state] = None

st.markdown('''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.1/css/all.min.css">
''', unsafe_allow_html=True)
st.write("Karten-Test")
st.markdown(
    f"""
    <style>

    [data-testid="stSidebar"]  {{
        background-color: rgb(240, 240, 242);
        width: 25%;
        float: left
    }}
    
     [data-testid="stAppViewBlockContainer"] {{
        margin: 0 auto;
    }}
	
    
    .item > a {{
        color: {primary_color};
        font-weight: bold;
    }}

    .tag {{
        display: inline-block;
        background-color: rgb(240, 240, 242);
        color: black;
        padding: 5px;
        margin: 2px;
        margin-bottom: 10px;
        border-radius: 3px;
       
    }}
    
    [data-testid="stSidebar"] [data-testid="stExpander"] {{
        background-color:  white;
        max-height: 400px !important;  /* Set the maximum height */
        overflow-y: auto !important;  /* Enable vertical scrolling */
        box-shadow: 2.5px 2.5px 5px rgba(0, 0, 0, 0.2);
    }}
    
    [data-testid="stExpander"] > details {{
        border-width: 0;
        border-style: none;
        border: none !important;
    
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] > details > summary  {{
        height: 120px;
    }}

     [data-testid="stSidebar"] [data-testid="stExpander"] > details > summary > span > div > p  {{
        font-size: 1rem;
        font-weight: bold;
        color: {primary_color};
        margin-bottom: 1em;
        text-align: left;
    }}

    [data-testid="stSidebar"] [data-testid="stExpander"] > details > summary > span > div > p:hover  {{
        text-decoration: underline;
    }}


    </style>


    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.title('Datensatz suchen')
    user_input = st.text_input("Suchbegriff eingeben")
    if st.button("Suchen", type="primary"):
        st.session_state['datasets'] = []
        results = search(user_input, 5)
        docs = {}
        for (score, address) in results.hits:
            doc = get_doc(address)
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
            st.session_state['datasets'].append(item_data)

    if st.session_state['datasets']:
        for flattened_item in st.session_state['datasets']:
            with st.expander(flattened_item['title']):
                st.markdown(f"[Link zur Quelle]({flattened_item['source_url']})")
                st.markdown(flattened_item['description'])
                st.markdown(ut.prepare_tags(flattened_item['umthes']), unsafe_allow_html=True)
            is_active = st.session_state["id"] == flattened_item["id"]


            if st.button('Mehr', key=flattened_item["id"]):
                st.session_state['id'] = flattened_item['id']
                st.session_state['dataset'] = flattened_item
                st.session_state['state'] = 1
                st.session_state['facets'] = None
        st.divider()

karten_test.show_karten_test()
