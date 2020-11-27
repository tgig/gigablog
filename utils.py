#
# utils
#
import markdown
import re
import yaml
import colorsys
import random
import os

import pdb

def my_renderer(text):
    wikid = wiki_me(text)
    pygmented_body = markdown.markdown(wikid, extensions=['codehilite', 'fenced_code', 'tables', 'wikilinks', 'nl2br'])
    return pygmented_body

def wiki_me(text):
    text = wiki_image(text)
    text = wiki_link(text)
    return text

def wiki_image(text):
    media = '/static/media/'
    # replace all wiki links ![[image.png]] with html
    return re.sub(r'\!\[\[(.*?)\]\]', '<img src="%s\\1" />' % media, text)

def wiki_link(text):
    paths = wikilinks_to_path(text)
    for path in paths:
        # if there is a pipe (|) in the link, only link the last bit of the text
        if "|" in path['file_name']:
            link_text = path['file_name'].split('|')[-1]
        else:
            link_text = path['file_name']

        text = text.replace("[[{}]]".format(path['file_name']), '<a href="/miki/{}.html">{}</a>'.format(path['url'], link_text))

    return text
    

def wikilinks_to_path(text):
    # find all links in the html and read into array
    links = re.findall(r'\[\[(.*?)\]\]', text)
    paths = []

    # for each link, replace with appropriate link
    for link in links:
        path = clean_node_path(link)
        paths.append(path)

    return paths



# look in the myriad of folders that hold content to try and find an image
def get_image_file(file, locs):
    # get a list of all the media files we have
    media_loc = ['static/media', 'content/miki']
    media_list = []

    for loc in media_loc:
        for root, subdirs, files in os.walk(loc):
            for f in files:
                if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.gif'):
                    if f == file:
                        return "{}/{}".format(root, f)

    return "static/img/nada.png"


def get_mikis_json_for_all_pages(flatpages, MIKI_DIR):
    mikis = [m for m in flatpages if m.path.startswith(MIKI_DIR)]
    # I need to deal with wikilinks, which flatpages does not like, so let's reset the meta for each page
    mikis = miki_reset_meta(mikis)
    mikis_json = miki_get_graph(mikis)
    return mikis_json


def get_miki_json_for_js(miki):

    miki = miki_reset_meta(miki)
    path = clean_node_path(miki.path)

    miki_json = { 
        "path": {
            "folderId": path['folder_id'], 
            "mikiId": path['miki_id'], 
            "folderName": path['folder_name'], 
            "fileName": path['file_name'], 
            "url": path['url']
        },
        "meta": miki.meta, 
        "html": miki.html 
    }
    return miki_json

def get_mikis_json_for_miki_id(miki_id, mikis_json):
    # we want to return any backlinks and forelinks that have anything to do with the passed in miki_id

    miki_index = next((index for (index, d) in enumerate(mikis_json['nodes']) if d['id'] == miki_id), None)

    # set the mass for the passed in miki_id so it rests in the center
    mikis_json['nodes'][miki_index]["mass"] = 10

    # find all links with source or target of this miki_id
    keep_links = [x for x in mikis_json['links'] if x['source'] == miki_id or x['target'] == miki_id]

    # remove every link not in the list
    mikis_json['links'] = keep_links

    # keep only nodes that are in the links
    keep_links_detail = [x['source'] for x in keep_links] + [x['target'] for x in keep_links]
    keep_nodes = [x for x in mikis_json['nodes'] if x['id'] in keep_links_detail]
    mikis_json['nodes'] = keep_nodes

    return mikis_json


# this function will remove the wikilinks [[brackets]] so the yaml meta does not think it is a list-in-a-list
def miki_reset_meta(mikis):
    if type(mikis) == list:
        for miki in mikis:
            miki = miki_reset_meta_work(miki)

        return mikis
    else:
        return miki_reset_meta_work(mikis)

# DRY
def miki_reset_meta_work(miki):
    # get path info for all links in meta
    paths = wikilinks_to_path(miki._meta)
    # replace
    for path in paths:
        miki._meta = miki._meta.replace("[[{}]]".format(path['file_name']), str(path))


    miki._meta = miki._meta.replace('#', '') # remove hash tags, they are invalid yaml
    
    if miki.meta:
        miki.meta = yaml.safe_load(miki._meta)

        # make sure the source, keywords, and relevant links are lists, not strings
        if 'source' in miki.meta.keys():
            if type(miki.meta['source']) == str or type(miki.meta['source']) == dict:
                miki.meta['source'] = [miki.meta['source']]
        
        if 'tags' in miki.meta.keys():
            if type(miki.meta['tags']) == str:
                miki.meta['tags'] = [miki.meta['tags']]
        
        if 'relevant' in miki.meta.keys():
            if type(miki.meta['relevant']) == str:
                miki.meta['relevant'] = [miki.meta['relevant']]

    
    return miki



# make an object with every page, it's metadata, and links
def miki_get_graph(mikis):
    folder_id = 0
    color = ""
    graph_json = {
        "nodes": [],
        "links": []
    }

    # loop through all pages and add nodes (pages) and edges (links)
    # order of ops:
        #   1. add node
        #   2. add edge
        #   3. add new nodes (from the edges)
    for miki in mikis:

        #######################################
        # 1. add node
        node_path = clean_node_path(miki.path)

        # get a new color if this is a new folder
        if color == "" or node_path['folder_id'] != folder_id:
            color = get_rand_color()
            folder_id = node_path['folder_id']

        # get json to append to the graph
        node_json = miki_get_graph_node_json(node_path, color)
        graph_json["nodes"].append(node_json)

        #######################################
        # 2. add edge
        meta_links = []

        # extract links out of source and relevant yaml tags, they should have already been modified to json
        if 'source' in miki.meta.keys():
            # if this is a dictionary and it has a link
            if type(miki.meta['source']) == dict and 'link' in miki.meta['source'].keys():
                meta_links.append(miki.meta['source']['link'])
            
            # if this is a list and has multiple dictionaries
            elif type(miki.meta['source']) == list:
                for s in miki.meta['source']:
                    if type(s) == dict:
                        meta_links.append(s['file_name'])



        if 'relevant' in miki.meta.keys():
            # if this is a dictionary and it has a link
            if type(miki.meta['relevant']) == dict and 'link' in miki.meta['relevant'].keys():
                meta_links.append(miki.meta['relevant']['link'])
            
            # if this is a list and has multiple dictionaries
            elif type(miki.meta['relevant']) == list:
                for obj in miki.meta['relevant']:
                    if type(obj) == dict:
                        meta_links.append(obj['file_name'])

        body_links = re.findall(r'\[\[(.*?)\]\]', miki.body)    # get links out of body text
        # comprehension to remove images from the list of links
        body_links = [x for x in body_links if 'png' not in x and 'jpg' not in x and 'gif' not in x]

        links = list(set(meta_links + body_links))              # merge w/o dups

        for link in links:
            node_link_path = clean_node_path(link)
            
            graph_json['links'].append({
                "source": node_path['miki_id'],
                "target": node_link_path['miki_id']
            })

    #######################################
    # 3. add new nodes (from the edges)
    node_ids = [node['id'] for node in graph_json['nodes']]
    for link in graph_json['links']:
        if link['source'] not in node_ids:
            node_path = clean_node_path(link['source'])
            node_json = make_graph_json_node(node_path, "#CCCCCC")
            graph_json["nodes"].append(node_json)
            node_ids.append(link['source'])

        if link['target'] not in node_ids:
            node_path = clean_node_path(link['target'])
            node_json = miki_get_graph_node_json(node_path, "#CCCCCC")
            graph_json["nodes"].append(node_json)
            node_ids.append(link['target'])

    return graph_json


def miki_get_graph_node_json(node_path, color):
    return {
        "id": node_path['miki_id'],
        "mass": 5,
        "color": color, 
        "origColor": color,
        "folderId": node_path['folder_id'], 
        "folderName": node_path['folder_name'],
        "fileName": node_path['file_name'],
        "url": node_path['url']
    }
    



# this works only because of my anal naming convention - every single file has a unique identifier in front of if
def clean_node_path(path):
    # if there is no folder system then just get the file name components
    if '/' not in path:
        folder_name = 'External'
        file_name = path
        miki_id = file_name.split(' ')[0]
        folder_id = 'External'
        url = "{}".format(miki_id)
    else:    
        bits = path.split('/')              # split into list

        folder_name = bits[-2]
        file_name = bits[-1]                # get the last bit with no folders
        miki_id = file_name.split(' ')[0]     # get the part with the decimal classification
        folder_id = miki_id.split('.')[0]
        url = "{}".format(miki_id)


    return {
        "folder_id": folder_id, 
        "miki_id": miki_id, 
        "folder_name": folder_name, 
        "file_name": file_name, 
        "url": url 
    } 


def get_rand_color():
    # inspiration: 
    # - https://stackoverflow.com/questions/43437309/get-a-bright-random-colour-python
    # - https://www.w3schools.com/colors/colors_hsl.asp
    #
    # I am fixing the saturation and lightness levels, randomizing the hue
    h,s,l = (random.randint(0, 360)/360), .78, .59
    r,g,b = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
    return '#%02x%02x%02x' % (r, g, b)
