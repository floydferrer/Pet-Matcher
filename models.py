from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ARRAY

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to provided Flask app"""

    db.app = app
    db.init_app(app)

class User(db.Model):
    """List of all Users who submitted a questionnaire. Can create an account to save results (optional)"""
    
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    experienced_owner = db.Column(
        db.Text,
        nullable=False,
    )
    
    kids = db.Column(
        db.Text,
        nullable=False,
    )
    
    dogs = db.Column(
        db.Text,
        nullable=False,
    )
    
    cats = db.Column(
        db.Text,
        nullable=False,
    )

    lifestyle = db.Column(
        db.Text,
        nullable=False
    )

    home_type = db.Column(
        db.Text,
        nullable=False
    )

    qualities = db.Column(
        db.Text,
        nullable=False
    )
    
    zip_code = db.Column(
        db.Integer,
        nullable=False
    )

    first_name = db.Column(
        db.Text,
        nullable=True
    )

    last_name = db.Column(
        db.Text,
        nullable=True
    )

    email = db.Column(
        db.Text,
        nullable=True,
        unique=True
    )
    
    password = db.Column(
        db.Text,
        nullable=True
    )
    
    search_url = db.Column(
        db.Text,
        nullable=False
    )

    @classmethod
    def signup(cls, experienced_owner, kids, dogs, cats, lifestyle, home_type, qualities, zip_code, first_name, last_name, email, password, search_url):
        """Sign up user. Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            experienced_owner=experienced_owner,
            kids=kids,
            dogs=dogs,
            cats=cats,
            lifestyle=lifestyle,
            home_type=home_type,
            qualities=qualities,
            zip_code=zip_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pwd,
            search_url=search_url
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, email, password):
        """Find user with `email` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Tag(db.Model):
    """List of all PetFinder API tags that have desricptions matching questionnaire parameters"""
    
    __tablename__ = 'tags'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    tag_name = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    pet_owner = db.Column(
        db.Text,
        nullable=True
    )

    lifestyle = db.Column(
        db.Text,
        nullable=True
    )

    home_size = db.Column(
        db.Text,
        nullable=True
    )

    qualities = db.Column(
        db.Text,
        nullable=True
    )
