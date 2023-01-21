from functools import wraps
from flask import request, abort
from AuthClient import AuthClient, UserDto
import jwt
from models import Chatter
from datetime import datetime, timedelta

def get_now():
    return datetime.utcnow().timestamp()

def token_required(f):
    token_cache = {}
    @wraps(f)
    def wrap(*args, **kwargs):
        # if request has no token, abort
        if not request.headers["authorization"]:
            abort(401)
        token = request.headers["authorization"].split(" ")[1]

        # Caching token
        # If we've validated this token before and it's not expired yet
        #  then proceed without calling auth endpoint
        # If we've validated this token before and it's expired
        #  then abort without calling auth endpoint
        if token in token_cache.keys() and token_cache[token]['exp'] > get_now():
            return f(*args, **kwargs, user_data=token_cache[token]['chatter']) 
        elif token in token_cache.keys() and token_cache[token]['exp'] <= get_now():
            abort(403)
        
        if not AuthClient.validate_token(token):
            abort(403)
        user_data = jwt.decode(token, options={"verify_signature": False})
        # get user via some ORM system
        # chatter = Chatter.query.filter(Chatter.username == user_data["username"]).one()
        token_cache[token] = {'exp': user_data['exp'], 'chatter': user_data}
        # make user available down the pipeline via flask.g
        # g.user = user
        # finally call f. f() now haves access to g.user
        return f(*args, **kwargs, user_data=user_data)
   
    return wrap

def token_validity_cache(f):
    token_dict = {}
    @wraps(f)
    def wrap(*args, **kwargs):
        # if request has no token, abort
        if not request.headers["authorization"]:
            abort(401)
        token = request.headers["authorization"].split(" ")[1]
        if not AuthClient.validate_token(token):
            abort(403)
        user_data = jwt.decode(token, options={"verify_signature": False})
        # get user via some ORM system
        # chatter = Chatter.query.filter(Chatter.username == user_data["username"]).one()
        # make user available down the pipeline via flask.g
        # g.user = user
        # finally call f. f() now haves access to g.user
        return f(*args, **kwargs, user_data=user_data)
   
    return wrap