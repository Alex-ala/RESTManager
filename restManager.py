import json
import os.path
from requests_oauthlib.oauth2_session import OAuth2Session
from flask import Flask, request, redirect, render_template
from wtforms import Form, TextAreaField

DATADIR = os.path.join(os.path.expanduser("~"),".rest_apis")
APIS = dict()

currentApi = dict()
app = Flask(__name__)

class CreateInputForm(Form):
    name = TextAreaField("Name")
    auth_uri = TextAreaField("Auth URL")
    token_uri = TextAreaField("Token URL")
    client_id = TextAreaField("Client ID")
    client_secret = TextAreaField("Client Secret")
    redirect_uri = TextAreaField("Redirect URL")
    scope = TextAreaField("Scope")


def load_configs():
    global APIS
    try:
        with open(os.path.join(DATADIR, ".apis")) as apiConfig:
            APIS = json.load(apiConfig)
    except:
        print("No config file yet")


def save_configs():
    with open(os.path.join(DATADIR, ".apis"), 'w+') as apiConfig:
        json.dump(APIS, apiConfig)


def createAPIToken(name, auth_uri, token_uri, client_id, client_secret, redirect_uri, scope):
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    auth, state = oauth.authorization_url(auth_uri)

    global currentApi
    api = dict()
    api["name"] = name
    api["auth_uri"] = auth_uri
    api["token_uri"] = token_uri
    api["client_id"] = client_id
    api["client_secret"] = client_secret
    api["redirect_uri"] = redirect_uri
    api["scope"] = scope

    currentApi = api
    return auth


@app.route("/",methods=['GET','POST'])
def main():
    form = CreateInputForm(request.form)
    if request.method == 'POST':
        url = createAPIToken(request.form['name'],request.form['auth_uri'],request.form['token_uri'],request.form['client_id'],request.form['client_secret'],request.form['redirect_uri'],request.form['scope'].split(","))
        return redirect(url)
    else:
        load_configs()
        apis = list()
        for key in APIS:
            apis.append(key)
        return render_template('restManager.html',form=form, apis=apis)


@app.route("/callback")
def callback():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    global currentApi
    print(currentApi)
    oauth = OAuth2Session(currentApi["client_id"], redirect_uri=currentApi["redirect_uri"], scope=currentApi["scope"])
    token = oauth.fetch_token(currentApi["token_uri"], client_secret=currentApi["client_secret"], authorization_response=request.url)
    currentApi["token"] = token
    global APIS
    APIS[currentApi["name"]]= currentApi
    save_configs()
    return redirect("/")


@app.route("/refresh")
def refresh():
    global APIS
    name = request.args.get("api")
    token = APIS[name]["token"]
    extra = {
        'client_id': APIS[name]["client_id"],
        'client_secret': APIS[name]["client_secret"],
    }

    oauth = OAuth2Session(APIS[name]["client_id"], token=token)
    APIS[name]["token"] = oauth.refresh_token(APIS[name]["token_uri"], **extra)
    save_configs()
    return redirect("/")

if __name__ == "__main__":
    app.run()
