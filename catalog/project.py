from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, session
import psycopg2
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item


# from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client import client, crypt
import httplib2
import json
from flask import make_response
import requests
app = Flask(__name__)

# engine = create_engine('sqlite:////vagrant/catalog/catalog/sitecatalog.db')
engine = create_engine('postgresql+psycopg2://postgres:Iamawesome1@localhost/sitecatalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
sess = DBSession()

secrets_loc = '/vagrant/catalog/catalog/client_secrets.json'
CLIENT_ID = json.loads(
    open(secrets_loc, 'r').read())['web']['client_id']
APPLICATION_NAME = "catalog-ac"


@app.route('/login')
def Login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/logout')
def Logout():
    if 'provider' in session:
        if session['provider'] == 'google':
            gdisconnect()
            del session['gplus_id']
            del session['access_token']
        # if session['provider'] == 'facebook':
        #     fbdisconnect()
        #     del session['facebook_id']
        del session['username']
        del session['email']
        del session['picture']
        del session['user_id']
        del session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('Landing'))
    else:
        flash("You were not logged in")
        return redirect(url_for('Login'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # check state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets(secrets_loc, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify correct user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = session.get('access_token')
    stored_gplus_id = session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                 'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session['access_token'] = credentials.access_token
    session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session['username'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']
    session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    print "1", user_id
    if not user_id:
        print "2", user_id
        user_id = createUser(session)
        print "3", user_id
    session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += session['username']
    output += '!</h1>'
    output += '<img src="'
    output += session['picture']
    output += """
              " style = "width: 300px; height: 300px;border-radius: 150px;
              -webkit-border-radius: 150px;-moz-border-radius: 150px;">
              """
    flash("you are now logged in as %s" % session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(session):
    newUser = User(name=session['username'], email=session[
                   'email'], picture=session['picture'])
    sess.add(newUser)
    sess.commit()
    user = sess.query(User).filter_by(email=session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = sess.query(User).filter_by(id=user_id).all()
    return user


def getUserID(email):
    try:
        user = sess.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/')
@app.route('/main')
def Landing():
    categories = sess.query(Category).all()
    items = sess.query(Item).limit(10).all()
    return render_template('main.html', categories=categories, items=items)


@app.route('/categories')
def Categories():
    categories = sess.query(Category).all()
    return render_template('categories.html', categories=categories)


@app.route('/category/<string:category>')
def ShowCategory(category):
    cat = sess.query(Category).filter_by(name=category).one()
    items = sess.query(Item).filter_by(category_id=cat.id).all()
    return render_template('itemList.html', items=items, category=cat)


@app.route('/category/create', methods=['GET', 'POST'])
def CreateCategory():
    if 'username' not in session:
        return redirect(url_for('Login'))
    if request.method == 'POST':
        newCat = Category(name=request.form['name'],
                          user_id=session['user_id'])
        sess.add(newCat)
        flash('New Category %s created' % newCat.name)
        sess.commit()
        return redirect(url_for('Categories'))
    else:
        return render_template('createCategory.html')


@app.route('/category/delete/<int:category_id>', methods=['GET', 'POST'])
def DeleteCategory(category_id):
    if 'username' not in session:
        return redirect(url_for('Login'))
    categoryToDelete = sess.query(Category).filter_by(id=category_id).one()
    itemsToDelete = sess.query(Item).filter_by(category_id=category_id).all()
    print itemsToDelete
    if session['username'] != categoryToDelete.user.name:
        return redirect(url_for('Login'))
    if request.method == 'POST':
        for i in itemsToDelete:
            sess.delete(i)
        sess.delete(categoryToDelete)
        sess.commit()
        return redirect(url_for('Landing'))
    else:
        category = sess.query(Category).filter_by(id=category_id).one()
        return render_template('deleteCategory.html', category=category)


@app.route('/item/newestItems')
def newestItems():
    items = sess.query(Item).limit(10).all()
    return render_template('newestItems.html', items=items)


@app.route('/item/<string:category>/<int:item_id>')
def ShowItem(category, item_id):
    item = sess.query(Item).filter_by(id=item_id).one()
    return render_template('item.html', item=item)


@app.route('/item/create', methods=['GET', 'POST'])
def CreateItem():
    if 'username' not in session:
        return redirect(url_for('Login'))
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       category_id=request.form['category'],
                       user_id=session['user_id'])
        sess.add(newItem)
        sess.commit()
        category_id = request.form['category']
        category = sess.query(Category).filter_by(id=category_id).one()
        return redirect(url_for('ShowCategory', category=category.name))
    else:
        cats = sess.query(Category).all()
        return render_template('createItem.html', categories=cats)


@app.route('/item/edit/<int:category_id>/<int:item_id>',
           methods=['GET', 'POST'])
def EditItem(category_id, item_id):
    if 'username' not in session:
        return redirect(url_for('Login'))
    itemToEdit = sess.query(Item).filter_by(id=item_id).one()
    cat = sess.query(Category).filter_by(id=category_id).one()
    categories = sess.query(Category).all()
    if session['username'] != itemToEdit.user.name:
        return redirect(url_for('Landing'))
    if request.method == 'POST':
        itemToEdit.name = request.form['name']
        itemToEdit.description = request.form['description']
        itemToEdit.price = request.form['price']
        # itemToEdit.category_id = request.form['category']
        sess.add(itemToEdit)
        sess.commit()
        return redirect(url_for('ShowCategory', category=cat.name))
    else:
        return render_template('editItem.html',
                               categories=categories,
                               item=itemToEdit)


@app.route('/item/delete/<int:category_id>/<int:item_id>',
           methods=['GET', 'POST'])
def DeleteItem(category_id, item_id):
    if 'username' not in session:
        return redirect(url_for('Login'))
    itemToDelete = sess.query(Item).filter_by(id=item_id).one()
    cat = sess.query(Category).filter_by(name=itemToDelete.category.name).one()
    if session['username'] != itemToDelete.user.name:
        return redirect(url_for('Login'))
    if request.method == 'POST':
        sess.delete(itemToDelete)
        sess.commit()
        return redirect(url_for('ShowCategory',
                                category=itemToDelete.category.name))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete,
                               category=cat)


@app.route('/catalog/json')
def CatalogJSON():
    categories = sess.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/category/<string:category>/json')
def CategoryJSON(category):
    cat = sess.query(Category).filter_by(name=category).one()
    return jsonify(Category=cat.serialize)


@app.route('/item/<int:item_id>/json')
def ItemJSON(item_id):
    item = sess.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    # app.secret_key = 'super_secret_key'
    app.debug = True
    # app.run(host='0.0.0.0', port=8000)
    app.run()
