#
# utils
#
import markdown
import re
import yaml
import colorsys
import random
import urllib.parse

import pdb

def my_renderer(text):
    #"""Inject the markdown rendering into the jinga template"""
    #rendered_body = render_template_string(text)
    wikid = wiki_me(text)    
    pygmented_body = markdown.markdown(wikid, extensions=['codehilite', 'fenced_code', 'tables', 'wikilinks'])
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
    return re.sub(r'\[\[(.*?)\]\]', '<a href="\\1">\\1</a>', text)



def get_mikis_json(flatpages, MIKI_DIR):
    mikis = [m for m in flatpages if m.path.startswith(MIKI_DIR)]
    # I need to deal with wikilinks, which flatpages does not like, so let's reset the meta for each page
    miki = miki_reset_meta(mikis)
    mikis_json = miki_extract(mikis)
    return mikis_json

def get_miki_json_for_js(miki, path):
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
    # for the future: this feels like it could be done much more efficiently...

    # set the mass for the passed in miki_id so it rests in the center
    mikis_json['nodes'][miki_id]["mass"] = 100

    # first go throug the edges and add any edge that references the passed in miki_id
    keep_me = [miki_id]
    for key in mikis_json['edges'].keys():
        if miki_id in mikis_json['edges'][key].keys():
            keep_me.append(key)

    # second remove edges that didn't match
    delete_me = set(mikis_json['edges'].keys()).difference(keep_me)
    for d in delete_me:
        mikis_json['edges'].pop(d, None)
    
    # third, find nodes to keep
    keep_me = [miki_id]
    for key in mikis_json['edges'].keys():
        keep_me.append(key)
        for sub_key in mikis_json['edges'][key].keys():
            keep_me.append(sub_key)
    
    # finally, remove the nodes that don't match
    delete_me = set(mikis_json['nodes'].keys()).difference(keep_me)
    for d in delete_me:
        mikis_json['nodes'].pop(d, None)

    # what is left over is only the nodes and edges that reference this miki_id

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
    miki._meta = re.sub(r'\[\[(.*?)\]\]', '{ "link": "\\1" }', miki._meta) # turn wikilinks into json
    miki._meta = miki._meta.replace('#', '') # remove hash tags, they are invalid yaml
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
def miki_extract(mikis):
    folder_id = 0
    color = ""
    graph_json = {
        "nodes": {},
        "edges": {}
    }

    # loop through all pages and add nodes (pages) and edges (links)
    # order of ops:
        #   1. add node
        #   2. add edge
        #   3. add edge children
    for miki in mikis:

        # 1. add node
        node_path = clean_node_path(miki.path)

        # get a new color if this is a new folder
        if color == "" or node_path['folder_id'] != folder_id:
            color = get_rand_color()
            folder_id = node_path['folder_id']

        graph_json["nodes"][node_path['miki_id']] = {
            "mass": 1,
            "color": color, 
            "origColor": color, 
            "folderId": node_path['folder_id'], 
            "mikiId": node_path['miki_id'],
            "folderName": node_path['folder_name'],
            "fileName": node_path['file_name'],
            "url": node_path['url']
        }

        # loop through keys and add each key to node_path
        # for tag in miki.meta:
        #     if miki.meta[tag]: # if the tag contents are not empty (None)
        #         graph_json["nodes"][node_path][tag] = miki.meta[tag]

        # 2. add edge
        graph_json["edges"][node_path['miki_id']] = {}

        meta_links = []
        
        # extract links out of source and relevant yaml tags, they should have already been modified to json
        if 'source' in miki.meta.keys():
            # if this is a dictionary and it has a link
            if type(miki.meta['source']) == dict and 'link' in miki.meta['source'].keys():
                meta_links.append(miki.meta['source']['link'])
            
            # if this is a list and has multiple dictionaries
            elif type(miki.meta['source']) == list:
                for obj in miki.meta['source']:
                    if type(obj) == dict:
                        meta_links.append(obj['link'])


        if 'relevant' in miki.meta.keys():
            # if this is a dictionary and it has a link
            if type(miki.meta['relevant']) == dict and 'link' in miki.meta['relevant'].keys():
                meta_links.append(miki.meta['relevant']['link'])
            
            # if this is a list and has multiple dictionaries
            elif type(miki.meta['relevant']) == list:
                for obj in miki.meta['relevant']:
                    if type(obj) == dict:
                        meta_links.append(obj['link'])



        body_links = re.findall(r'\[\[(.*?)\]\]', miki.body)    # get links out of body text
        links = list(set(meta_links + body_links))              # merge w/o dups

        for link in links:
            node_link_path = clean_node_path(link)
            graph_json['edges'][node_path['miki_id']].update({ node_link_path['miki_id']: {}})



    # are there edges that don't exist in nodes? Add them
    # for edge in graph_json['edges']:
    #     if edge[1] not in graph_json['nodes']:
    #         graph_json['nodes'].append(edge[1])

    return graph_json


# this works only because of my anal naming convention - every single file has a unique identifier in front of if
def clean_node_path(path):
    # if there is no folder system then just get the file name components
    try:
        if '/' not in path:
            folder_name = 'External'
            file_name = path
            miki_id = file_name.split(' ')[0]
            folder_id = 'External'
            url = urllib.parse.quote("external-file/{}".format(file_name))
        else:    
            bits = path.split('/')              # split into list

            folder_name = bits[-2]
            file_name = bits[-1]                # get the last bit with no folders
            miki_id = file_name.split(' ')[0]     # get the part with the decimal classification
            folder_id = miki_id.split('.')[0]
            url = urllib.parse.quote("{}/{}".format(folder_name, file_name))
    except:
        pdb.set_trace()

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
