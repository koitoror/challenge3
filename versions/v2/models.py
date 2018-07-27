import uuid
from versions import db
from passlib.hash import sha256_crypt


class User(db.Model):
    """Create table users
    One-to-Many relationship with entry and diary
    User has many diariess
    User has many entries
    delete-orphan to delete any attached child
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    fullname = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    hash_key = db.Column(db.String(), unique=True, nullable=False)
    activate = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    diaries = db.relationship(
        'Diary',
        backref='owner',
        cascade='all, delete-orphan'
    )
    entries = db.relationship(
        'Entry',
        backref='entryer',
        cascade='all, delete-orphan'
    )
    notifications = db.relationship(
        'Notification',
        backref='recipient',
        cascade='all, delete-orphan'
    )

    def __init__(self, username, fullname, email, password):
        """Sets defaults for creating user instance
        sets username and email to lower case
        encrypts password
        generates a random hash key
        sets activate to false, this will be changed later
        """
        self.username = username.lower().strip()
        self.fullname = fullname
        self.email = email.lower().strip()
        self.password = sha256_crypt.encrypt(str(password))
        self.hash_key = uuid.uuid1().hex
        self.activate = False

    def save(self):
        """Commits user instance to the database"""
        db.session.add(self)
        db.session.commit()


class Diary(db.Model):
    """Create table diaries
    One-to-Many relationship with entry and user
    diary belongs to user
    diary has many entries
    """
    __tablename__ = 'diaries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), index=True)
    logo = db.Column(db.String())
    location = db.Column(db.String(), index=True)
    category = db.Column(db.String(), index=True)
    bio = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    entries = db.relationship(
        'Entry',
        backref='diary',
        cascade='all, delete-orphan'
    )

    def __init__(self, name=None, logo=None, location=None,
                 category=None, bio=None, owner=None):
        self.name = name
        self.logo = logo
        self.location = location
        self.category = category
        self.bio = bio
        self.owner = owner

    def Search(self, params):
        """Search and filter"""
        page = params['page']
        limit = params['limit']
        location = params['location']
        category = params['category']
        _query = params['_query']

        if _query or location or category:
            if location and _query and not category:
                return self.query.filter(
                    Diary.location == location,
                    Diary.name.ilike('%' + _query + '%')
                ).paginate(page, limit, error_out=False).items

            if category and _query and not location:
                return self.query.filter(
                    Diary.category == category,
                    Diary.name.ilike('%' + _query + '%')
                ).paginate(page, limit, error_out=False).items

            if category and location and not _query:
                return self.query.filter(
                    Diary.location == location,
                    Diary.category == category
                ).paginate(page, limit, error_out=False).items

            if location and not _query and not category:
                return self.query.filter(
                    Diary.location == location
                ).paginate(page, limit, error_out=False).items

            if category and not _query and not location:
                return self.query.filter(
                    Diary.category == category
                ).paginate(page, limit, error_out=False).items

            return self.query.filter(
                Diary.name.ilike('%' + _query + '%')
            ).paginate(page, limit, error_out=False).items

        return self.query.order_by(
            Diary.created_at.desc()
        ).paginate(page, limit, error_out=False).items

    def save(self):
        """Save a diary to the database"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete a given diary"""
        db.session.delete(self)
        db.session.commit()


class Entry(db.Model):
    """Create table entries
    One-to-Many relationship with user and diary
    entry belongs to diary
    entry belongs to user
    """
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String())
    desc = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    diary_id = db.Column(
        db.Integer,
        db.ForeignKey('diaries.id'),
        nullable=False
    )

    def __init__(self, title, desc, diary, entryer):
        self.title = title
        self.desc = desc
        self.diary = diary
        self.entryer = entryer

    def save(self):
        """Save a entry to the database"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete a given entry."""
        db.session.delete(self)
        db.session.commit()


class Notification(db.Model):
    """Handles notifications when user entries on a diary"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    actor = db.Column(db.String(), nullable=False)
    diary_id = db.Column(db.Integer, nullable=False)
    entry_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(), nullable=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, recipient, actor, diary_id, entry_id, read_at=None):
        self.recipient = recipient
        self.actor = actor
        self.diary_id = diary_id
        self.entry_id = entry_id
        self.read_at = read_at
        self.action = ' entryed one of your diaries'

    def save(self):
        """Save a entry to the database"""
        db.session.add(self)
        db.session.commit()

class AuthToken(db.Model):
    """Stores all tokens during login"""
    __tablename__ = 'authtokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(), nullable=False)
    valid = db.Column(db.Boolean, nullable=False)

    def __init__(self, token, valid=True):
        self.token = token
        self.valid = valid

    def save(self):
        """Save a entry to the database"""
        db.session.add(self)
        db.session.commit()
    