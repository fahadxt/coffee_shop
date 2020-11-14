import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# uncomment the following line to initialize the datbase
db_drop_and_create_all()


# endpoint for all available drinks, and show short details about a drink
@app.route('/drinks', methods=['GET'])
def drinks_index():
    drinks = Drink.query.order_by(Drink.id).all()
    drinks = [drink.short() for drink in drinks]

    return jsonify({
      'success': True,
      'drinks': drinks,
    })


# endpoint for show detail a drink, and require permission 'get:drinks-detail'
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drink_detail(payload):
    drinks = Drink.query.order_by(Drink.id).all()
    drinks = [drink.long() for drink in drinks]

    return jsonify({
      'success': True,
      'drinks': drinks,
    })


# endpoint for new drink (store), and require the 'post:drinks' permission
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def drink_store(payload):
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)

    try:
        drink = Drink(
            title=title,
            recipe=json.dumps(recipe)
        )
        drink.insert()

        return jsonify({
            'success': True,
            "drinks": drink.long()
        })

    except BaseException:
        abort(422)


# endpoint for update a drink, and require the 'patch:drinks' permission
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def drink_update(payload, id):
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    try:
        title = body.get('title')
        recipe = body.get('recipe')

        if title:
            drink.title = title

        if recipe:
            drink.recipe = json.dumps(recipe)

        drink.update()

    except BaseException:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


# endpoint for destroy a drink, and require the 'delete:drinks' permission
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def drink_destroy(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    try:
        drink.delete()

    except BaseException:
        abort(400)

    return jsonify({'success': True, 'delete': id}), 200


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request'
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


# error handler for AuthError
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
