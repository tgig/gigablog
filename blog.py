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
MIKI_DIR = 'MIKI'
FLATPAGES_HTML_RENDERER = utils.my_renderer

app = Flask(__name__)
flatpages = FlatPages(app)
freezer = Freezer(app)
app.config.from_object(__name__)


### ROUTES ###

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/posts/")
def posts():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    posts.sort(key=itemgetter('date'), reverse=True)
    return render_template('posts.html', posts=posts)

@app.route('/posts/<name>/')
def post(name):
    path = '{}/{}'.format(POST_DIR, name)
    post = flatpages.get_or_404(path)
    return render_template('post.html', post=post)

@app.route("/miki/")
def miki():
    # get all mikis to start with
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    return render_template('mikis.html', mikis=mikis_json)

@app.route("/miki/<file>/")
def miki_page(file):
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    
    # find the folder and file name to get
    this_miki = next((item for item in mikis_json['nodes'] if item['id'] == file), None)
    if this_miki:
        # this file does exist
        folder_name = this_miki['folderName']
        file_name = this_miki['fileName']
    else:
        #folder_name = "no_url_for_you"
        file_name = "no_url_for_you"

    path = '{}/{}/{}'.format(MIKI_DIR, folder_name, file_name)
    miki = flatpages.get_or_404(path)
    
    miki_json = utils.get_miki_json_for_js(miki)
    mikis_json = utils.get_mikis_json_for_miki_id(miki_json['path']['mikiId'], mikis_json)

    return render_template('miki.html', miki=miki_json, mikis=mikis_json)

# @app.route('/miki/external-file/<file>/')
# def external_file(file):
#     return render_template('external-file.html', file=file)

@app.route('/contact/')
def contact_page():
    return render_template('contact.html')

@app.route('/site-map/')
def site_map():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    
    mikis = sorted(mikis_json['nodes'], key=itemgetter('id'))

    return render_template('site-map.html', posts=posts, mikis=mikis, today=date.today())

@app.route('/site-map.xml')
def site_map_xml():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    #return render_template('site-map.xml', posts=posts, mikis=mikis_json, today=date.today())

    template = render_template('site-map.xml', posts=posts, mikis=mikis_json, today=date.today())
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'

    return response


### NON PAGE ROUTES ###

# @app.route("/miki/json/<miki_id>/")
# def return_miki_json(miki_id):
#     # get all mikis to start with
#     mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)

#     # if this is a specific miki page, then restrict the full list down to only nodes/links that reference this file
#     if miki_id != "all":
#         mikis_json = utils.get_mikis_json_for_miki_id(miki_id, mikis_json)

#     return mikis_json

# @app.route("/miki/find-page/<file>/")
# def find_page(file):

#     mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
#     node_path = utils.clean_node_path(file)

#     # find the folder and file name to get
#     this_miki = next((item for item in mikis_json['nodes'] if item['id'] == node_path['miki_id']), None)
#     if this_miki:
#         # this file does exist, so get it and redirect
#         folder_name = this_miki['folderId']
#         file_name = this_miki['id']

#         #return render_template('miki.html', miki_json=miki_json, mikis_json=mikis_json)
#         return redirect('/{}/{}/{}'.format(MIKI_DIR.lower(), folder_name, file_name))

#     else:
#         return redirect('/miki/external-file/{}'.format(file))


@app.route('/media/<file>')
def media_file(file):

    media_loc = ['static/media', '{}/{}'.format(FLATPAGES_ROOT, POST_DIR), '{}/{}'.format(FLATPAGES_ROOT, MIKI_DIR)]
    file_loc = utils.get_image_file(file, media_loc)
    return send_file(file_loc)


@freezer.register_generator
def freeze_miki_pages():

    #delete existing files in the /build dir


    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis = utils.get_mikis_json(flatpages, MIKI_DIR)

    
    # get all posts
    for post in posts:
        yield '/{}/'.format(post.path)
    
    #pdb.set_trace()

    for miki in mikis['nodes']:
        yield '/miki/{}/'.format(miki['url'])



### MAIN ###

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host='0.0.0.0', port=8000, debug=True)
