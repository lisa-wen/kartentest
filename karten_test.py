import streamlit as st
from service import embedding, search, get_doc
import folium
from streamlit_folium import st_folium
import utils as ut
import toml
import branca
import json
from branca.colormap import LinearColormap

germany_location = [51.1657, 10.4515]
config = toml.load('.streamlit/config.toml')
primary_color = config['theme']['primaryColor']
primary_button = config['theme']['primaryButton']
secondary_button = config['theme']['secondaryButton']
marker_color = "#ef9850"
RECOMMENDATION_NUM = 25
gradient_colors = ut.generate_monochromatic_gradient(primary_color, RECOMMENDATION_NUM)
gradient_css = ", ".join(gradient_colors)
path_dataset = "M215.7 499.2C267 435 384 279.4 384 192C384 86 298 0 192 0S0 86 0 192c0 87.4 117 243 168.3 307.2c12.3 15.3 35.1 15.3 47.4 0zM192 128a64 64 0 1 1 0 128 64 64 0 1 1 0-128z"
path_recommendation = "M16 144a144 144 0 1 1 288 0A144 144 0 1 1 16 144zM160 80c8.8 0 16-7.2 16-16s-7.2-16-16-16c-53 0-96 43-96 96c0 8.8 7.2 16 16 16s16-7.2 16-16c0-35.3 28.7-64 64-64zM128 480l0-162.9c10.4 1.9 21.1 2.9 32 2.9s21.6-1 32-2.9L192 480c0 17.7-14.3 32-32 32s-32-14.3-32-32z"


def show_karten_test():
    legend_html = f"""
        {{% macro html(this, kwargs) %}} 
        <style>
        #legend {{
            position: fixed;
            bottom: 30px;  
            left: 10px;    
            width: 40px; 
            height: 300px; 
            background-color: white;
            font-size: 10px;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            padding: 5px;
            z-index: 99999;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 2px solid #d3d3d3;
        }}

        #legend .gradient-bar {{
            flex: 1;
            width: 100%;
            height: 100%;
            background: linear-gradient(to top, {gradient_css});
            border-radius: 10px;
        }}
        #legend .legend-label {{
            font-size: 10px;
            text-align: center;
            color: {primary_color};
            margin: 5px 0;
        }} 

        .leaflet-control-layers {{
            background-color: #ffffff !important;
            border-radius: 5px;
            box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .leaflet-control-layers-label {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .leaflet-control-layers-selector {{
            background-color: #ffffff !important;
            opacity: 1 !important;
            border-radius: 5px;
        }}

        </style>
        <div id="legend">
            <div class="legend-label">sehr ähnlich</div>
            <div class="gradient-bar"></div>
            <div class="legend-label">weniger ähnlich</div>
        </div>
        {{% endmacro %}} 
    """

    m = folium.Map(location=germany_location, zoom_start=6, tiles=None)

    folium.TileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        name='Basis Ansicht',
        attr='Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    ).add_to(m)

    folium.TileLayer(
        'cartodb positron',
        name='Helle Ansicht',
        attr='Tiles by CartoDB, under CC BY 3.0.',
    ).add_to(m)

    legend = branca.element.MacroElement()
    legend._template = branca.element.Template(legend_html)
    m.get_root().add_child(legend)

    st.title("Karten-Test")
    fg_dataset = folium.FeatureGroup(name=f"{ut.get_svg(marker_color, path_dataset, 16)} Aktueller Datensatz")
    fg_recommendations = folium.FeatureGroup(name=f"{ut.get_svg(primary_color, path_recommendation, 16)} Empfehlung")
    colormap = LinearColormap(
        colors=gradient_colors,
        vmin=0,
        vmax=1,
        caption="Monochromatic Gradient")

    if st.session_state['id']:
        dataset = ut.flatten_item(st.session_state["dataset"])
        st.write('Ihr gewählter Datensatz:', help="Test")
        html_title = f'<p class="item"><a href="{dataset["source_url"]}">{dataset["title"]}</a></p>'
        tags = ut.prepare_tags(dataset["umthes"])
        description = f'<div class="item">{dataset["description"]}</div>'
        st.markdown(html_title, unsafe_allow_html=True)
        with st.expander('Mehr...'):
            st.markdown(description, unsafe_allow_html=True)
            st.markdown(f'<div class="item">{tags}', unsafe_allow_html=True)

        with st.spinner("Bitte warten..."):
            if 'bounding_boxes' in dataset and dataset['bounding_boxes'] is not None:
                folium.Marker(
                    location=ut.set_marker(dataset["bounding_boxes"][0]),
                    icon=ut.get_svg_icon(marker_color, path_dataset, 30),
                    opacity=1,
                    tooltip='Aktueller Datensatz'
                ).add_to(fg_dataset)
            else:
                st.markdown(
                    f"""
                    <div style="
                        padding: 10px; 
                        border-radius: 5px; 
                        background-color: {primary_color}; 
                        color: white; 
                        font-weight: bold;">
                        ⚠️ Leider liegen keine Koordinaten für den ausgewählten Datensatz vor.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            fg_dataset.add_to(m)

            st.session_state['map_recommendations'] = embedding(st.session_state['id'], RECOMMENDATION_NUM+1)
            st.toast('Empfehlungen generiert')

            i = 1
            for recommendation in st.session_state['map_recommendations']:
                rec_id = recommendation['id']

                if 'bounding_boxes' in recommendation and recommendation['bounding_boxes']:
                    try:
                        (score, address) = search(f'"{rec_id}"', 1, ['id']).hits[0]
                        doc = get_doc(address)
                    except Exception as e:
                        print('An error occured while getting extra information for recommendations!')
                        continue
                    bounding_box = recommendation['bounding_boxes'][0]
                    marker = ut.set_marker(bounding_box)
                    value = 1 - i / RECOMMENDATION_NUM
                    color = colormap(value)
                    quality_block = "<div>No quality score</div>"
                    fair_block = json.loads(doc['fair'][0])
                    if fair_block['score']:
                        quality_block = ut.get_stars(fair_block['score'])

                    def prepare_data_type(files):
                        if not files:
                            return "keine Angabe"
                        try:
                            file_types = json.loads(files[0])
                            labels = [item['type']['label'] for item in file_types if 'type' in item]
                            unique_labels = sorted(set(labels))
                            return ", ".join(unique_labels) if unique_labels else "keine Angabe"
                        except Exception as e:
                            print(f"Fehler bei Datentyp-Extraktion: {e}")
                            return "keine Angabe"

                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.1/css/all.min.css"
                        rel="stylesheet">
                    </head>
                    <body>
                        <p style="font-size: 18px; font-weight: bold; color:{primary_color};">{recommendation['title']}</p>
                        {quality_block}
                           <span title="Bewertung basierend auf FAIR-Kriterien (Metadatenqualität)."> 
                                <i class="fa-regular fa-circle-question" style="color:{primary_button}; margin-left: 5px;"></i>
                           </span>
                           <br></br>
                           <p style="max-height: 120px; overflow-y: auto; padding-right: 10px; color: #333; line-height: 1.4;">{recommendation['description']}</p>
                            <p style="color: #A9A9A9; margin-bottom: 5px;">Herkunft: {doc["portals"][0].split('/')[1] if doc["portals"] else "Unbekannt"}</p>
                            <p style="color: #A9A9A9; margin-top: 0px; margin-bottom: 10px;">Ressourcen: {prepare_data_type(doc['files'])}</p>
                        {f'<a href="{recommendation.get("source_url")}" target="_blank"><i class="fa-solid fa-up-right-from-square" style="color: {primary_button};"></i></a>' if recommendation.get("source_url") else ""}
                    </body>
                    </html>
                    """
                    folium.Marker(
                        location=marker,
                        icon=ut.get_svg_icon(color, path_recommendation, 30),
                        tooltip=recommendation['title'],
                        popup=folium.Popup(html, max_width=250)
                    ).add_to(fg_recommendations)
                    i = i + 1

            fg_recommendations.add_to(m)
            colormap.add_to(m)
            folium.map.LayerControl('topleft', collapsed=True).add_to(m)
            st_folium(m, width=1000, height=600, returned_objects=[])
            st.toast('Kartenansicht geladen')