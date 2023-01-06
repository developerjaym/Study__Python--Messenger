from functools import wraps
from flask import request, abort
from AuthClient import AuthClient, UserDto
import jwt
from models import Chatter

def token_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        print("$$$$$$$$$$$$$$$$ tokenRequired", request.headers["authorization"])
        # if request has no token, abort
        if not request.headers["authorization"]:
            abort(401)
        token = request.headers["authorization"].split(" ")[1]
        if not AuthClient.validate_token(token):
            abort(403)
        print("jwt token probs", token)
        user_data = jwt.decode(token, options={"verify_signature": False})
        # get user via some ORM system
        print('user_data from jwt', user_data)
        chatter = Chatter.query.filter(Chatter.username == user_data["username"]).one()
        # make user available down the pipeline via flask.g
        # g.user = user
        # finally call f. f() now haves access to g.user
        return f(*args, **kwargs, chatter=chatter)
   
    return wrap
