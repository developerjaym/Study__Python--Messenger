#!/usr/bin/env python3

from AuthDecorators import token_required
from flask import Flask, jsonify, request, make_response, Response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_cors import CORS
from models import db, Chatter, Game
from AuthClient import AuthClient, UserDto

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
# we need this for some reason
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False


migrate = Migrate(app, db)

db.init_app(app)  # do not forget this line !!!
api = Api(app)

ma = Marshmallow(app)  # be sure this line comes after the db stuff


class ChatterSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Chatter
        load_instance = True

    username = ma.auto_field()

    url = ma.Hyperlinks(
        {
            "self": ma.URLFor(
                "chatterbyusername",
                values=dict(username="<username>")),
            "collection": ma.URLFor("chatters"),
        }
    )
chatter_schema = ChatterSchema()
chatters_schema = ChatterSchema(many=True)


class GameSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Game
        load_instance = True

    name = ma.auto_field()
    link = ma.auto_field()
    image = ma.auto_field()

    url = ma.Hyperlinks(
        { #TODO
            # "self": ma.URLFor(
            #     "gamesbyusernameandname",
            #     values=dict(username="<username>", name="<name>")),
            # "collection": ma.URLFor("games"),
        }
    )
game_schema = GameSchema()
games_schema = GameSchema(many=True)

class Chatters(Resource):

    @token_required
    def get(self, chatter):

        chatters = Chatter.query.order_by(Chatter.username.asc()).all()

        response = make_response(
            chatters_schema.dump(chatters),
            200,
        )

        return response

    def post(self):
        response = AuthClient.post_account(request.json)
        # TODO handle exception
        new_chatter = Chatter(
            username=request.json['username']
        )
        db.session.add(new_chatter)
        db.session.commit()

        response = make_response(
            response,
            # chatter_schema.dump(new_chatter),
            201,
        )

        return response


api.add_resource(Chatters, '/chatters')


class ChatterByUsername(Resource):

    def get(self, username):

        chatter = Chatter.query.filter_by(username=username).first()

        response = make_response(
            chatter_schema.dump(chatter),
            200,
        )

        return response

    def patch(self, username):
        #TODO
        chatter = Chatter.query.filter_by(username=username).first()
        for attr in request.form:
            setattr(chatter, attr, request.form[attr])

        db.session.add(chatter)
        db.session.commit()

        response = make_response(
            chatter_schema.dump(chatter),
            200
        )

        return response

    def delete(self, username):
        #TODO
        record = Chatter.query.filter_by(username=username).first()

        db.session.delete(record)
        db.session.commit()

        response_dict = {"message": "record successfully deleted"}

        response = make_response(
            response_dict,
            200
        )

        return response


api.add_resource(ChatterByUsername, '/chatters/<string:username>')

class ChatterTokenByUsername(Resource):

    def post(self, username):
        response = AuthClient.get_token(request.headers["authorization"])
        # TODO handle exception

        response = make_response(
            response,
            # chatter_schema.dump(new_chatter),
            201,
        )

        return response


api.add_resource(ChatterTokenByUsername, '/chatters/<string:username>/token')

class ChatterFriendsByUsername(Resource):
    @token_required
    def get(self, username, chatter):
        return make_response(chatters_schema.dump(chatter.friends), 200,)

    @token_required
    def post(self, username, chatter):
        print("$$$$$$$$$", request.json)
        # TODO stop users from adding themselves as friends
        # TODO stop users from adding friends they already have
        friend = Chatter.query.filter(Chatter.username == request.json['friend']).one()
        chatter.friends.append(friend)
        db.session.commit()

        response = make_response(
            chatters_schema.dump(chatter.friends),
            201,
        )

        return response


api.add_resource(ChatterFriendsByUsername, '/chatters/<string:username>/friends')

class GamesByUsername(Resource):

    @token_required
    def get(self, username, chatter):
        print('username', username)
        print('chatter', chatter)
        # chatter = Chatter.query.filter_by(username=username).first()

        response = make_response(
            games_schema.dump(chatter.games),
            200,
        )

        return response

    @token_required    
    def post(self, username, chatter):
        #TODO verify username in URL matches chatter's username
        new_game = Game(name=request.json["name"], link=request.json["link"], image=request.json["image"], chatter=chatter)
        db.session.add(new_game)
        db.session.commit()

        response = make_response(
            game_schema.dump(new_game),
            201,
        )

        return response

api.add_resource(GamesByUsername, '/chatters/<string:username>/games')
#TODO post games, get games by user id


if __name__ == '__main__':
    app.run(port=5555)
