#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

user_schema = UserSchema()
recipe_schema = RecipeSchema()


class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio', '')
        image_url = data.get('image_url', '')

        if not username:
            return {'error': 'Username is required.'}, 422

        user = User(username=username, bio=bio, image_url=image_url)
        try:
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists.'}, 422
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

        session['user_id'] = user.id
        return user_schema.dump(user), 201


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Unauthorized'}, 401
        return user_schema.dump(user), 200


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter(User.username == username).first()
        if not user or not user.authenticate(password):
            return {'error': 'Invalid credentials.'}, 401

        session['user_id'] = user.id
        return user_schema.dump(user), 200


class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        session['user_id'] = None
        return {}, 204


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        recipes = Recipe.query.filter(Recipe.user_id == user_id).all()
        return [recipe_schema.dump(r) for r in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id,
            )
            db.session.add(recipe)
            db.session.commit()
        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return {'error': str(e)}, 422

        return recipe_schema.dump(recipe), 201


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)