from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
app = Flask(__name__)

engine = create_engine('sqlite:///sitecatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
sess = DBSession()


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
    return render_template('itemList.html', items=items)


@app.route('/category/create', methods=['GET', 'POST'])
def CreateCategory():
    if request.method == 'POST':
        newCat = Category(name=request.form['name'])
        sess.add(newCat)
        flash('New Category %s created' % newCat.name)
        sess.commit()
        return redirect(url_for('Categories'))
    else:
        return render_template('createCategory.html')


@app.route('/category/delete/<int:category_id>', methods=['GET', 'POST'])
def DeleteCategory(category_id):
    if request.method == 'POST':
        categoryToDelete = sess.query(Category).filter_by(id=category_id).one()
        sess.delete(categoryToDelete)
        sess.commit()
        return redirect(url_for('Landing'))
    else:
        category = sess.query(Category).filter_by(id=category_id).one()
        return render_template('deleteCategory.html', category=category)


@app.route('/item/<string:category>/<int:item_id>')
def ShowItem(category, item_id):
    item = sess.query(Item).filter_by(id=item_id).one()
    return render_template('item.html', item=item)


@app.route('/item/create', methods=['GET', 'POST'])
def CreateItem():
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       category_id=request.form['category'])
        sess.add(newItem)
        sess.commit()
        category_id = request.form['category']
        category = sess.query(Category).filter_by(id=category_id).one()
        return redirect(url_for('ShowCategory', category=category.name))
    else:
        cats = sess.query(Category).all()
        return render_template('createItem.html', categories=cats)


@app.route('/item/edit/<int:category_id>/<int:item_id>', methods=['GET', 'POST'])
def EditItem(category_id, item_id):
    itemToEdit = sess.query(Item).filter_by(id=item_id).one()
    cat = sess.query(Category).filter_by(id=category_id).one()
    categories = sess.query(Category).all()
    if request.method == 'POST':
        itemToEdit.name = request.form['name']
        itemToEdit.description = request.form['description']
        itemToEdit.price = request.form['price']
        # itemToEdit.category_id = request.form['category']
        sess.add(itemToEdit)
        sess.commit()
        return redirect(url_for('ShowCategory', category=cat.name))
    else:
        return render_template('editItem.html', categories=categories, item=itemToEdit)


@app.route('/item/delete/<int:category_id>/<int:item_id>', methods=['GET', 'POST'])
def DeleteItem(category_id, item_id):
    itemToDelete = sess.query(Item).filter_by(id=item_id).one()
    cat = sess.query(Category).filter_by(name=itemToDelete.category.name).one()
    if request.method == 'POST':
        sess.delete(itemToDelete)
        sess.commit()
        return redirect(url_for('ShowCategory', category=itemToDelete.category.name))
    else:
        return render_template('deleteItem.html', item=itemToDelete, category=cat)


@app.route('/catalog/json')
def CatalogJSON():
    items = sess.query(Item).group_by(Item.category_id).all()
    return jsonify(Catalog=[i.serialize for i in items])


@app.route('/category/<string:category>/json')
def CategoryJSON(category):
    cat = sess.query(Category).filter_by(name=category).one()
    items = sess.query(Item).filter_by(category_id=cat.id).all()
    return jsonify(Category_items=[i.serialize for i in items])


@app.route('/item/<int:item_id>/json')
def ItemJSON(item_id):
    item = sess.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)

@app.route('/test')
def test():
    return render_template('tester.html')

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
