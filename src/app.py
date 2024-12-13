import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Favorite, People

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# Endpoints de People
@app.route('/people', methods=['GET', 'POST'])
def get_or_add_people():
    if request.method == 'GET':
        all_people = People.query.all()
        people_serialized = [person.serialize() for person in all_people]
        return jsonify({"data": people_serialized}), 200
    elif request.method == 'POST':
        body = request.get_json()
        new_person = People(
            name=body.get('name'),
            height=body.get('height'),
            mass=body.get('mass'),
            hair_color=body.get('hair_color'),
            skin_color=body.get('skin_color'),
            eye_color=body.get('eye_color'),
            birth_year=body.get('birth_year'),
            gender=body.get('gender')
        )
        db.session.add(new_person)
        db.session.commit()
        return jsonify({"msg": "Nuevo personaje agregado", "data": new_person.serialize()}), 201

@app.route('/people/<int:people_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"msg": f"El personaje con id {people_id} no existe"}), 404
    if request.method == 'GET':
        return jsonify({"data": person.serialize()}), 200
    elif request.method == 'PUT':
        body = request.get_json()
        person.name = body.get('name', person.name)
        person.height = body.get('height', person.height)
        person.mass = body.get('mass', person.mass)
        person.hair_color = body.get('hair_color', person.hair_color)
        person.skin_color = body.get('skin_color', person.skin_color)
        person.eye_color = body.get('eye_color', person.eye_color)
        person.birth_year = body.get('birth_year', person.birth_year)
        person.gender = body.get('gender', person.gender)
        db.session.commit()
        return jsonify({"msg": "Personaje actualizado", "data": person.serialize()}), 200
    elif request.method == 'DELETE':
        db.session.delete(person)
        db.session.commit()
        return jsonify({"msg": "Personaje eliminado"}), 200

# Endpoints de Planets
@app.route('/planets', methods=['GET', 'POST'])
def get_or_add_planet():
    if request.method == 'GET':
        all_planets = Planet.query.all()
        planets_serialized = [planet.serialize() for planet in all_planets]
        return jsonify({"data": planets_serialized}), 200
    elif request.method == 'POST':
        body = request.get_json()
        new_planet = Planet(
            name=body.get('name'),
            population=body.get('population')
        )
        db.session.add(new_planet)
        db.session.commit()
        return jsonify({"msg": "Nuevo planeta agregado", "data": new_planet.serialize()}), 201

@app.route('/planets/<int:planet_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": f"El planeta con id {planet_id} no existe"}), 404
    if request.method == 'GET':
        return jsonify({"data": planet.serialize()}), 200
    elif request.method == 'PUT':
        body = request.get_json()
        planet.name = body.get('name', planet.name)
        planet.population = body.get('population', planet.population)
        db.session.commit()
        return jsonify({"msg": "Planeta actualizado", "data": planet.serialize()}), 200
    elif request.method == 'DELETE':
        db.session.delete(planet)
        db.session.commit()
        return jsonify({"msg": "Planeta eliminado"}), 200

# Endpoints de Favorites
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.json.get('user_id', None)
    if not user_id:
        return jsonify({"msg": "El user_id es requerido"}), 400
    
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": f"El planeta con id {planet_id} no existe"}), 404
    
    favorite = Favorite(user_id=user.id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"msg": "Planeta agregado a favoritos"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user_id = request.json.get('user_id', None)
    if not user_id:
        return jsonify({"msg": "El user_id es requerido"}), 400
    
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"msg": f"El personaje con id {people_id} no existe"}), 404
    
    favorite = Favorite(user_id=user.id, people_id=people_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"msg": "Personaje agregado a favoritos"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user_id = request.json.get('user_id', None)
    if not user_id:
        return jsonify({"msg": "El user_id es requerido"}), 400
    
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if favorite is None:
        return jsonify({"msg": f"El favorito con id de personaje {people_id} no existe"}), 404
    
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Personaje eliminado de favoritos"}), 200


@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.json.get('user_id', None)
    if not user_id:
        return jsonify({"msg": "El user_id es requerido"}), 400
    
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    favorites_serialized = [favorite.serialize() for favorite in favorites]
    return jsonify({"data": favorites_serialized}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
