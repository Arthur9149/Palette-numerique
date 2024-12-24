import requests
from bs4 import BeautifulSoup
import json
import os
from PIL import Image
from io import BytesIO

def fetch_and_save_artworks(artist_name, path, language='english'):
    """
    Function: Fetch and save artworks URLs and titles from WikiArt.
    Fonction : Récupérer et enregistrer les URLs et les titres des œuvres depuis WikiArt.

    In:
        - artist_name (str): The name of the artist. / Le nom de l'artiste.
        - path (str): The path to the folder where the files will be saved. / Le chemin vers le dossier où les fichiers seront enregistrés.
        - language (str): The language for the artworks titles (default is 'english'). / La langue des titres des œuvres (par défaut 'english').

    Out:
        - (str): The path to the JSON file containing the artworks URLs. / Le chemin vers le fichier JSON contenant les URLs des œuvres.
    """
    lang_path = '/en/' if language == 'english' else '/fr/'
    artist_slug = artist_name.lower().replace(' ', '-')
    url = f"https://www.wikiart.org{lang_path}{artist_slug}/all-works/text-list"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print("This artist is not in the WikiArt database or there is a typo.")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    list_items = soup.select('li.painting-list-text-row a')
    artworks = [{'title': a.text.strip(), 'href': a['href']} for a in list_items]
    
    def get_unique_filename(base_path, base_name, ext):
        counter = 1
        new_path = os.path.join(base_path, f"{base_name}{ext}")
        while os.path.exists(new_path):
            new_path = os.path.join(base_path, f"{base_name}_{counter:02}{ext}")
            counter += 1
        return new_path

    suffix = '_en' if language == 'english' else '_fr'
    titles_path = get_unique_filename(path, f'artworks_titles{suffix}', '.txt')
    links_path = get_unique_filename(path, f'artworks_webpage_urls{suffix}', '.json')
    
    with open(titles_path, 'w', encoding='utf-8') as f:
        for artwork in artworks:
            f.write(f"{artwork['title']}\n")
    
    with open(links_path, 'w', encoding='utf-8') as f:
        json.dump([artwork['href'] for artwork in artworks], f, ensure_ascii=False, indent=4)
    
    print(f"Artworks titles have been saved to {titles_path}")
    print(f"Artworks links have been saved to {links_path}")
    
    return links_path

def download_imgs(json_file, path):
    """
    Function: Download images of the artworks from their URLs.
    Fonction : Télécharger les images des œuvres à partir de leurs URLs.

    In:
        - json_file (str): The path to the JSON file containing the artworks URLs. / Le chemin vers le fichier JSON contenant les URLs des œuvres.
        - path (str): The path to the folder where the images will be saved. / Le chemin vers le dossier où les images seront enregistrées.

    Out:
        - None
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
    download_path = os.path.join(path, 'download_imgs')
    os.makedirs(download_path, exist_ok=True)
    
    base_url = "https://www.wikiart.org"
    
    total_urls = len(urls)
    print(f"Downloading images (total: {total_urls})...")
    
    for i, url in enumerate(urls):
        full_url = base_url + url
        response = requests.get(full_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', itemprop='image')
        if img_tag:
            img_url = img_tag['src']
            img_data = requests.get(img_url).content
            img_name = os.path.join(download_path, f"image_{i+1}.jpg")
            with open(img_name, 'wb') as img_file:
                img_file.write(img_data)
            print(f"Downloaded ({i+1}/{total_urls}) : {img_name}")
        else:
            print(f"Image not found for URL: {full_url}")

def get_color(urls):
    """
    Function: Extract the first pixel color from images at the given URLs.
    Fonction : Extraire la couleur du premier pixel des images aux URLs données.

    In:
        - urls (list): A list of URLs of the artworks. / Une liste d'URLs des œuvres.

    Out:
        - colors (list): A list of RGB color tuples. / Une liste de tuples de couleurs RGB.
    """
    colors = []
    base_url = "https://www.wikiart.org"
    
    total_urls = len(urls)
    print(f"Extracting colors (total: {total_urls})...")
    
    for i, url in enumerate(urls):
        full_url = base_url + url
        response = requests.get(full_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', itemprop='image')
        if img_tag:
            img_url = img_tag['src']
            img_data = requests.get(img_url).content
            img = Image.open(BytesIO(img_data)).convert('RGB')  # Convert to RGB mode
            first_pixel = img.resize((1, 1)).getpixel((0, 0))
            colors.append(first_pixel)
        print(f"Color extracted ({i+1}/{total_urls})")
    return colors

def rgb_to_hex(rgb):
    """
    Function: Convert an RGB color tuple to a hexadecimal color string.
    Fonction : Convertir un tuple de couleur RGB en une chaîne de couleur hexadécimale.

    In:
        - rgb (tuple): An RGB color tuple. / Un tuple de couleur RGB.

    Out:
        - (str): A hexadecimal color string. / Une chaîne de couleur hexadécimale.
    """
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def hex_to_hsl(hex_color):
    """
    Function: Convert a hexadecimal color string to HSL (hue, saturation, lightness).
    Fonction : Convertir une chaîne de couleur hexadécimale en HSL (teinte, saturation, luminosité).

    In:
        - hex_color (str): A hexadecimal color string. / Une chaîne de couleur hexadécimale.

    Out:
        - (tuple): An HSL color tuple. / Un tuple de couleur HSL.
    """
    r = int(hex_color[1:3], 16) / 255.0
    g = int(hex_color[3:5], 16) / 255.0
    b = int(hex_color[5:7], 16) / 255.0
    max_color = max(r, g, b)
    min_color = min(r, g, b)
    l = (max_color + min_color) / 2
    if max_color == min_color:
        s = 0
        h = 0
    else:
        if l < 0.5:
            s = (max_color - min_color) / (max_color + min_color)
        else:
            s = (max_color - min_color) / (2.0 - max_color - min_color)
        if max_color == r:
            h = (g - b) / (max_color - min_color)
        elif max_color == g:
            h = 2.0 + (b - r) / (max_color - min_color)
        else:
            h = 4.0 + (r - g) / (max_color - min_color)
    return (h * 60) % 360, s, l

def luminance(rgb):
    """
    Function: Calculate the luminance of an RGB color.
    Fonction : Calculer la luminance d'une couleur RGB.

    In:
        - rgb (tuple): An RGB color tuple. / Un tuple de couleur RGB.

    Out:
        - (float): The luminance of the color. / La luminance de la couleur.
    """
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_unique_svg_filename(base_path, base_name, ext):
    """
    Function: Get a unique filename by appending a counter if the file already exists.
    Fonction : Obtenir un nom de fichier unique en ajoutant un compteur si le fichier existe déjà.

    In:
        - base_path (str): The base path to the folder. / Le chemin de base vers le dossier.
        - base_name (str): The base name of the file. / Le nom de base du fichier.
        - ext (str): The file extension. / L'extension du fichier.

    Out:
        - (str): A unique filename with a counter appended if necessary. / Un nom de fichier unique avec un compteur ajouté si nécessaire.
    """
    counter = 1
    new_path = os.path.join(base_path, f"{base_name}{ext}")
    while os.path.exists(new_path):
        new_path = os.path.join(base_path, f"{base_name}_{counter:02}{ext}")
        counter += 1
    return new_path

def convert_to_svg(colors, svg_filename, hex_codes_file, mode="basic"):
    """
    Function: Convert the extracted colors to an SVG file and save it.
    Fonction : Convertir les couleurs extraites en un fichier SVG et l'enregistrer.

    In:
        - colors (list): A list of RGB color tuples. / Une liste de tuples de couleurs RGB.
        - svg_filename (str): The base name of the SVG file. / Le nom de base du fichier SVG.
        - hex_codes_file (str): The path to the folder where the SVG and hex codes list will be saved. / Le chemin vers le dossier où seront enregistrés le fichier SVG et la liste des codes hexadécimaux.
        - mode (str): The mode of color classification ('basic', 'shade', 'luminance'). / Le mode de classification des couleurs ('basic', 'shade', 'luminance').

    Out:
        - None
    """
    hex_colors = [rgb_to_hex(color) for color in colors]

    if mode == "shade":
        hex_colors.sort(key=lambda c: (hex_to_hsl(c)[0], hex_to_hsl(c)[1]))
    elif mode == "luminance":
        hex_colors.sort(key=lambda c: luminance((int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))))
    
    num_colors = len(hex_colors)
    side_length = int(num_colors**0.5)
    if side_length**2 < num_colors:
        side_length += 1

    svg_header = '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">'.format(side_length * 100, side_length * 100)
    svg_footer = '</svg>'
    svg_content = ''

    for idx, hex_color in enumerate(hex_colors):
        x = (idx % side_length) * 100
        y = (idx // side_length) * 100
        svg_content += f'<rect x="{x}" y="{y}" width="100" height="100" fill="{hex_color}"/>'

    svg_image = svg_header + svg_content + svg_footer

    output_path = get_unique_svg_filename(hex_codes_file, svg_filename, '.svg')
    with open(output_path, 'w') as file:
        file.write(svg_image)
    print(f"SVG saved to: {output_path}")

    hex_output_path = get_unique_svg_filename(hex_codes_file, 'hex_codes_list', '.txt')
    with open(hex_output_path, 'w') as file:
        for hex_color in hex_colors:
            file.write(hex_color + '\n')
    print(f"Hex codes list saved to: {hex_output_path}")

def url_to_canva(artist_name, path, download_images=False, mode="basic", language="english"):
    """
    Function: Fetch artworks, optionally download images, extract colors, and save to SVG.
    Fonction : Récupérer des œuvres, télécharger éventuellement des images, extraire des couleurs et les enregistrer en SVG.

    In:
        - artist_name (str): The name of the artist. / Le nom de l'artiste.
        - path (str): The path to the folder where files will be saved. / Le chemin vers le dossier où les fichiers seront enregistrés.
        - download_images (bool): Whether to download the images (default is False). / Si les images doivent être téléchargées (par défaut False).
        - mode (str): The mode of color classification ('basic', 'shade', 'luminance'). / Le mode de classification des couleurs ('basic', 'shade', 'luminance').
        - language (str): The language for the artworks titles (default is 'english'). / La langue des titres des œuvres (par défaut 'english').

    Out:
        - None
    """
    json_file = fetch_and_save_artworks(artist_name, path, language)
    if json_file is None:
        return

    if download_images:
        download_imgs(json_file, path)
    
    if mode == "shade":
        svg_filename = "palette_shade"
    elif mode == "luminance":
        svg_filename = "palette_luminance"
    else:
        svg_filename = "palette_basic"
    
    with open(json_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
    colors = get_color(urls)
    convert_to_svg(colors, svg_filename, path, mode=mode)

# Example usage with user inputs
artist_name = input("Enter the artist's name: ")
path = input("Enter the folder path: ")
download_images = input("Do you want to download the artworks? (yes/no): ").lower() == 'yes'
mode = input("Color classification mode (basic/shade/luminance): ").lower()
if mode not in ["basic", "shade", "luminance"]:
    mode = "basic"
language = input("Language of artworks titles (may be not translated) (english/français): ").lower()
if language not in ["english", "français"]:
    language = "english"

url_to_canva(artist_name, path, download_images, mode, language)
