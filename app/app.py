#!/usr/bin/env python3

from AuthDecorators import token_required
from flask import Flask, jsonify, request, make_response, Response, abort
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from flask_cors import CORS
from models import db, Chatter, Game, Message, Conversation
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

class MessageSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Message
        load_instance = True

    timestamp = ma.auto_field()
    content = ma.auto_field()
    author = ma.Nested(chatter_schema)
    id = ma.auto_field()
    #TODO get author in here???

    url = ma.Hyperlinks(
        { #TODO
            # "self": ma.URLFor(
            #     "gamesbyusernameandname",
            #     values=dict(username="<username>", name="<name>")),
            # "collection": ma.URLFor("games"),
        }
    )
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)

class ConversationSchema(ma.SQLAlchemySchema):

    class Meta:
        model = Conversation
        load_instance = True

    id = ma.auto_field()
    chatters = ma.Nested(chatters_schema)
    # messages = ma.Nested(messages_schema)
    #TODO get messages in here???

    url = ma.Hyperlinks(
        { #TODO
            # "self": ma.URLFor(
            #     "gamesbyusernameandname",
            #     values=dict(username="<username>", name="<name>")),
            # "collection": ma.URLFor("games"),
        }
    )
conversation_schema = ConversationSchema()
conversations_schema = ConversationSchema(many=True)



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
        if chatter.username != username:
            abort(403)
        
        return make_response(chatters_schema.dump(Chatter.query.filter(Chatter.username == chatter.username).one().friends), 200,)

    @token_required
    def post(self, username, chatter):
        print("$$$$$$$$$", request.json)
        # TODO stop users from adding themselves as friends
        # TODO stop users from adding friends they already have
        if chatter.username != username:
            abort(403)
        adder_friend = Chatter.query.filter(Chatter.username == chatter.username).one()    
        friend = Chatter.query.filter(Chatter.username == request.json['friend']).one()
        adder_friend.friends.append(friend)
        db.session.commit()

        response = make_response(
            chatters_schema.dump(adder_friend.friends),
            201,
        )

        return response


api.add_resource(ChatterFriendsByUsername, '/chatters/<string:username>/friends')

class DeleteFriendByUsernameAndFriendUsername(Resource):

    @token_required
    def delete(self, username, friend, chatter):
        if chatter.username != username:
            abort(403)
        #TODO
        # Delete friendship
        # Delete conversations containing both of these users
        chatter = Chatter.query.filter(Chatter.username == chatter.username).one()
        chatter.friends = [chatter_friend for chatter_friend in chatter.friends if chatter_friend.username != friend]
        friend_chatter = Chatter.query.filter(Chatter.username == friend).one()
        friend_chatter.friends =  [chatter_friend for chatter_friend in friend_chatter.friends if chatter_friend.username != friend]
        shared_conversations = find_conversations_with_these_two(chatter, friend_chatter)
        [db.session.delete(shared_conversation) for shared_conversation in shared_conversations]
        db.session.commit()

api.add_resource(DeleteFriendByUsernameAndFriendUsername, '/chatters/<string:username>/friends/<string:friend>')

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

def find_conversations_with_these_two(chatter_a, chatter_b):
    return set(set(chatter_a.conversations) & set(chatter_b.conversations))

class ConversationsByUsername(Resource):

    @token_required
    def get(self, username, chatter):
        print('username', username)
        print('chatter', chatter)
        if chatter.username != username:
            abort(403)

        chatter = Chatter.query.filter(Chatter.username==chatter.username).first()
        if "with" in request.args.keys():
            and_contains_this_guy = Chatter.query.filter(Chatter.username == request.args["with"]).first()
            results = find_conversations_with_these_two(and_contains_this_guy, chatter)#set(set(and_contains_this_guy.conversations) & set(chatter.conversations))
        else:
            results = chatter.conversations    
            

        response = make_response(
            conversations_schema.dump(results),
            200,
        )

        return response

    @token_required    
    def post(self, username, chatter):
        #TODO verify username in URL matches chatter's username
        #TODO filter duplicates from the 
        # the request will include the usernames of the chatters
        # take those usernames, construct the conversation, add, commit
        print('just started chat with', request.json, chatter)
        chatters = Chatter.query.filter(Chatter.username.in_(request.json)).all()
        chatters.append(chatter)
        print('found these matches', chatters)
        new_conversation = Conversation(chatters = chatters, messages = [])
        db.session.add(new_conversation)
        db.session.commit()

        response = make_response(
            conversation_schema.dump(new_conversation),
            201,
        )

        return response

api.add_resource(ConversationsByUsername, '/chatters/<string:username>/conversations')

class ConversationsByUsernameAndId(Resource):

    @token_required
    def get(self, username, id, chatter):
        print('username', username)
        print('chatter', chatter)
        #TODO error handling
        response = make_response(
            conversation_schema.dump(Conversation.query.filter(Conversation.id == id).one()),
            200,
        )

        return response

api.add_resource(ConversationsByUsernameAndId, '/chatters/<string:username>/conversations/<int:id>')


class MessagesByUsernameAndConversationId(Resource):

    @token_required
    def post(self, username, id, chatter):
        print('username', username)
        print('chatter', chatter)
        new_message = Message(conversation_id=id, author_id = chatter.id, content=request.json['content'])
        db.session.add(new_message)
        db.session.commit()
        #TODO error handling
        response = make_response(
            message_schema.dump(new_message),
            200,
        )

        return response

    @token_required
    def get(self, username, id, chatter):
        print(request.args['after'])
        after_id = request.args['after']
        new_messages = Message.query.filter(Message.conversation_id == id, Message.id > after_id).all()
        return make_response(messages_schema.dump(new_messages), 200,)

api.add_resource(MessagesByUsernameAndConversationId, '/chatters/<string:username>/conversations/<int:id>/messages')



if __name__ == '__main__':
    app.run(port=5555)
