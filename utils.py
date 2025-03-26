import toml
import folium
from item import Item
from item import Umthes
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb
import matplotlib.colors as mcolors

config = toml.load('.streamlit/config.toml')
primary_color = config['theme']['primaryColor']
primary_button = config['theme']['primaryButton']

def flatten_item(item: Item) -> dict:
    item['description'] = item['description'] if item['description'] else ''
    return item


def set_bounding_box(bounding_box: str):
    lat1 = bounding_box['min']['y']
    lon1 = bounding_box['min']['x']
    lat2 = bounding_box['max']['y']
    lon2 = bounding_box['max']['x']
    # Create a folium map
    m = folium.Map(location=[(lat1 + lat2) / 2, (lon1 + lon2) / 2], zoom_start=13)

    # Add a bounding box
    bounds = [[lat1, lon1], [lat2, lon2]]
    folium.Rectangle(bounds=bounds, color=primary_button, fill_color="blue", fill=True, fill_opacity=0.2).add_to(m)

    return m


def set_marker(bounding_box: str):
    lat1 = bounding_box['min']['y']
    lon1 = bounding_box['min']['x']
    lat2 = bounding_box['max']['y']
    lon2 = bounding_box['max']['x']
    return [(lat1 + lat2) / 2, (lon1 + lon2) / 2]


def prepare_tags(tags) -> str:
    tags_html = "<div>"
    #print(tags)
    if tags is not None:
        for tag_raw in tags:
            tag = tag_raw['label']
            tags_html += f'<span class="tag">{tag}</span>'
        tags_html += "</div>"
    return tags_html


def print_data(recommendation) -> str:
    html_data = (f'<div class="rec" id="scrollableContent">'
                 f'<p class="title">{recommendation["title"]}</p>'
                 f'<a href="{recommendation["source_url"]}">Link zur Quelle</a>'
                    f'<p>{recommendation["description"]}</p>'
                 f'{prepare_tags(recommendation["umthes"])}'
                 f'</div>')
    return html_data


def process_item(json_obj) -> Item:
    print(json_obj)
    item_data = {
        "id": json_obj['id'],
        "title": json_obj['title'],
    }

    if 'tags_json' in json_obj and json_obj['tags_json']:
        umthes_list = [Umthes(**tag['Umthes']) for tag in json_obj['tags_json']['json'] if 'Umthes' in tag]
        item_data['umthes'] = umthes_list

    if 'source_url' in json_obj:
        item_data['source_url'] = json_obj['source_url']

    return item_data


def get_svg(color, path, size):
    html = f"""
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" width="{size}px" height="{size}px">
                <path d="{path}"
                      filter="url(#change-color)" fill="{color}"/>
            </svg>
        """
    return html


def get_svg_icon(color, path, size):
    html = get_svg(color, path, size)
    return folium.DivIcon(html=html)


def get_stars(score):
    full_star = '<i class="fa-solid fa-star" style="color: #8D88C1; font-size: 24px;"></i>'
    half_star = '<i class="fa-solid fa-star-half-stroke" style="color: #8D88C1; font-size: 24px;"></i>'
    empty_star = '<i class="fa-regular fa-star" style="color: #8D88C1; font-size: 24px;"></i>'
    rating = score * 5
    # Generate stars based on the rating
    stars = ""
    for i in range(1, 6):  # Iterate over 5 stars
        if rating >= i:
            stars += full_star  # Add a full star
        elif i - 1 < rating < i:
            stars += half_star  # Add a half star if between values
        else:
            stars += empty_star  # Add an empty star

    return f'<div style="display: inline-block;">{stars}</div>'

def generate_monochromatic_gradient(hex_color, n_shades):
    rgb = mcolors.hex2color(hex_color)  # Returns (R, G, B) tuple
    hsv = rgb_to_hsv(rgb)  # Convert to HSV

    # Fix the hue and saturation of the base color
    hue, saturation, base_lightness = hsv

    # Generate gradient by varying lightness
    gradient = []
    for i in range(n_shades):
        # Linearly vary lightness from 100% (lightest) to the base lightness (10%)
        new_lightness = 1.0 - i * (1.0 - base_lightness) / n_shades
        new_color_hsv = (hue, saturation, new_lightness)  # Keep hue and saturation constant
        new_color_rgb = hsv_to_rgb(new_color_hsv)
        gradient.append(mcolors.to_hex(new_color_rgb))

    return gradient







