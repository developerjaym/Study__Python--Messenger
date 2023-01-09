from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

friendship_table = db.Table('frienships',
                    db.Column('left_id', db.Integer, db.ForeignKey('chatters.id'), primary_key=True),
                    db.Column('right_id', db.Integer, db.ForeignKey('chatters.id'), primary_key=True)
                    )

chatter_conversation = db.Table('chatter_conversation',
                    db.Column('chatter_id', db.Integer, db.ForeignKey('chatters.id')),
                    db.Column('conversation_id', db.Integer, db.ForeignKey('conversations.id'))
                    )

class Chatter(db.Model):
    __tablename__ = 'chatters'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)

    games = db.relationship('Game', backref='chatter')
    # Referenced https://stackoverflow.com/questions/9116924/how-can-i-achieve-a-self-referencing-many-to-many-relationship-on-the-sqlalchemy
    # (The creator sqlalchemy gave the top answer)
    friends = db.relationship("Chatter", secondary=friendship_table, 
                           primaryjoin=id==friendship_table.c.left_id,
                           secondaryjoin=id==friendship_table.c.right_id,
    )

    def __repr__(self):
        return f'<Chatter {self.username}>'


friendship_union = db.select([
                        friendship_table.c.left_id, 
                        friendship_table.c.right_id
                        ]).union(
                            db.select([
                                friendship_table.c.left_id, 
                                friendship_table.c.right_id]
                            )
                    ).alias()
Chatter.all_friends = db.relationship('Chatter',
                       secondary=friendship_union,
                       primaryjoin=Chatter.id==friendship_union.c.left_id,
                       secondaryjoin=Chatter.id==friendship_union.c.right_id,
                       viewonly=True) 

class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    link = db.Column(db.String)
    image = db.Column(db.String)


    chatter_id = db.Column(db.Integer, db.ForeignKey('chatters.id'))

    def __repr__(self):
        return f'<Game {self.name}, {self.link}, {self.image}>'

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    chatters = db.relationship('Chatter', secondary=chatter_conversation, backref='conversations')
    # one-to-many (one conversation to many messages)
    messages = db.relationship('Message', backref=db.backref('conversation'))

    def __repr__(self):
        return f'<Conversation {self.id}>'

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    content = db.Column(db.String)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    author_id = db.Column(db.Integer, db.ForeignKey('chatters.id'))
    author = db.relationship('Chatter', backref=db.backref('messages'))


    def __repr__(self):
        return f'<Message {self.content}>'
