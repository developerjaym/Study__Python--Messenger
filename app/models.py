from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Chatter(db.Model):
    __tablename__ = 'chatters'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)

    games = db.relationship('Game', backref='chatter')

    def __repr__(self):
        return f'<Chatter {self.username}>'

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    link = db.Column(db.String)
    image = db.Column(db.String)


    chatter_id = db.Column(db.Integer, db.ForeignKey('chatters.id'))

    def __repr__(self):
        return f'<Game {self.name}, {self.link}, {self.image}>'