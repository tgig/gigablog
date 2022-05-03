import sys
from operator import itemgetter
from flask import Flask, render_template, redirect, send_file, make_response
from flask_flatpages import FlatPages, pygments_style_defs
from flask_frozen import Freezer
import utils
from datetime import date

import pdb


DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = ['.md', '.html']
FLATPAGES_ROOT = 'content'
POST_DIR = 'posts'
MIKI_DIR = 'miki'
MIKI_DIR_FOLDER_EXCLUDE = '115'
FLATPAGES_HTML_RENDERER = utils.my_renderer

app = Flask(__name__)
flatpages = FlatPages(app)
freezer = Freezer(app)
app.config.from_object(__name__)


### ROUTES ###

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")

@app.route("/")
def index():
    mikis_json = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR)
    folder_json = utils.get_mikis_folders(mikis_json['nodes'])
    # remove excluded folders from graph
    mikis_json = utils.filter_ignored_mikis(mikis_json, MIKI_DIR_FOLDER_EXCLUDE)
    
    return render_template('index.html', mikis=mikis_json, folders=folder_json)

@app.route("/posts.html")
def posts():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    posts.sort(key=itemgetter('date'), reverse=True)
    return render_template('posts.html', posts=posts)

@app.route('/posts/<name>.html')
def post(name):
    path = '{}/{}'.format(POST_DIR, name)
    post = flatpages.get_or_404(path)
    
    return render_template('post.html', post=post)

@app.route("/miki/<file>.html")
def miki_page(file):
    mikis_json = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR)
    
    # find the folder and file name to get
    this_miki = next((item for item in mikis_json['nodes'] if item['id'] == file), None)
    if this_miki:
        # this file does exist
        folder_name = this_miki['folderName']
        file_name = this_miki['fileName']
    else:
        folder_name = "no_url_for_you"
        file_name = "no_url_for_you"

    path = '{}/{}/{}'.format(MIKI_DIR, folder_name, file_name)
    miki = flatpages.get_or_404(path)
    
    miki_json = utils.get_miki_json_for_js(miki)
    mikis_json = utils.get_mikis_graph_for_miki_ids([miki_json['path']['mikiId']], mikis_json)

    return render_template('miki.html', miki=miki_json, mikis=mikis_json)

@app.route("/miki/folder/<folder>.html")
def miki_folder(folder):
    mikis_json = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR)

    # loop through and get all the files in this folder
    files_json = []

    for miki in mikis_json['nodes']:
        if miki['folderId'] == folder:
                files_json.append(miki)
    
    #files_json = dict(sorted(files_json.items())) # sort
    files_json.sort(key=itemgetter('id'))

    # get nodes and links for graph
    miki_ids = [x['id'] for x in files_json]
    mikis_json = utils.get_mikis_graph_for_miki_ids(miki_ids, mikis_json)

    return render_template('miki-folder.html', files=files_json, folder=files_json[0], mikis=mikis_json)
    

@app.route('/contact.html')
def contact_page():
    return render_template('contact.html')

@app.route('/site-map.html')
def site_map():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    posts.sort(key=itemgetter('date'), reverse=True)

    mikis_json = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR)
    mikis = sorted(mikis_json['nodes'], key=itemgetter('id'))

    return render_template('site-map.html', posts=posts, mikis=mikis, today=date.today())

@app.route('/site-map.xml')
def site_map_xml():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis_json = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR)

    template = render_template('site-map.xml', posts=posts, mikis=mikis_json, today=date.today())
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'

    return response


### NON PAGE ROUTES ###

@app.route('/static/media/<file>')
def media_file(file):

    media_loc = ['static/media', '{}/{}'.format(FLATPAGES_ROOT, POST_DIR), '{}/{}'.format(FLATPAGES_ROOT, MIKI_DIR)]
    file_loc = utils.get_image_file(file, media_loc)
    return send_file(file_loc)


@freezer.register_generator
def freeze_miki_pages():
    import os
    import shutil

    # copy all images that are int the /content folders to the /static/media folder
    for root, subdirs, files in os.walk('content/'):
        for f in files:
            if f.endswith('.png') or f.endswith('.jpg') or f.endswith('.gif') or f.endswith('.mp4'):
                shutil.copy('{}/{}'.format(root, f), 'build/static/media/{}'.format(f))
                
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]   # get posts
    mikis = utils.get_mikis_json_for_all_pages(flatpages, MIKI_DIR) # get miki pages

    # get all posts
    for post in posts:
        yield '/{}.html'.format(post.path)

    folder_id = ""
    for miki in mikis['nodes']:
        yield '/miki/{}.html'.format(miki['url'])

        if miki['folderId'] != folder_id:
            yield '/miki/folder/{}.html'.format(miki['folderId'])


### MAIN ###

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        # verbose, will output every file to the log
        for page in freezer.freeze_yield():
            print(page.url)
    else:
        app.run(host='0.0.0.0', port=8000, debug=True)
