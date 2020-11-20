import sys
from operator import itemgetter
from flask import Flask, render_template, redirect
from flask_flatpages import FlatPages, pygments_style_defs
from flask_frozen import Freezer
import utils
from datetime import date

import pdb


DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'
FLATPAGES_ROOT = 'content'
POST_DIR = 'posts'
MIKI_DIR = 'miki'
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
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    return render_template('mikis.html', mikis_json=mikis_json)

@app.route("/miki/<folder>/<file>")
def miki_page(folder, file):
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    
    # find the folder and file name to get
    if file in mikis_json['nodes'].keys():
        # this file does exist, so get it and redirect
        folder_name = mikis_json['nodes'][file]['folderName']
        file_name = mikis_json['nodes'][file]['fileName']
    else:
        folder_name = "no_url_for_you"
        file_name = "no_url_for_you"

    path = '{}/{}/{}'.format(MIKI_DIR, folder_name, file_name)
    miki = flatpages.get_or_404(path)
    
    miki = utils.miki_reset_meta(miki)
    miki.html = utils.miki_reset_html_links(miki.html)
    path = utils.clean_node_path(miki.path)
    miki_json = utils.get_miki_json_for_js(miki, path)
    mikis_json = utils.get_mikis_json_for_miki_id(path['miki_id'], mikis_json) # restrict mikis_json to only nodes that reference this file

    return render_template('miki.html', miki_json=miki_json, mikis_json=mikis_json)

@app.route('/miki/external-file/<file>')
def external_file(file):
    return render_template('external-file.html', file=file)

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/site-map')
def site_map():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    # sort by node key
    mikis = {}
    for key in sorted(mikis_json['nodes'].keys()):
        mikis[key] = mikis_json['nodes'][key]

    return render_template('site-map.html', posts=posts, mikis=mikis, today=date.today())

@app.route('/site-map.xml')
def site_map_xml():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    return render_template('site-map.xml', posts=posts, mikis=mikis_json, today=date.today())

### NON PAGE ROUTES ###

@app.route("/miki/find-page/<file>")
def find_page(file):
    mikis_json = utils.get_mikis_json(flatpages, MIKI_DIR)
    node_path = utils.clean_node_path(file)

    if node_path['miki_id'] in mikis_json['nodes'].keys():
        # this file does exist, so get it and redirect
        folder_name = mikis_json['nodes'][node_path['miki_id']]['folderId']
        file_name = mikis_json['nodes'][node_path['miki_id']]['mikiId']

        #return render_template('miki.html', miki_json=miki_json, mikis_json=mikis_json)
        return redirect('/{}/{}/{}'.format(MIKI_DIR, folder_name, file_name))

    else:
        return redirect('/miki/external-file/{}'.format(file))

    


### MAIN ###

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host='0.0.0.0', port=8000, debug=True)

