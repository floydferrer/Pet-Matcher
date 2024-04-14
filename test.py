import os
from unittest import TestCase

from models import db, User, Tag

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///pet_matcher_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test user."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()
    
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            experienced_owner='1',
            kids='2',
            dogs='3',
            cats='4',
            lifestyle='5',
            home_type='6',
            qualities=['7','8','9'],
            zip_code=12345,
            first_name='test',
            last_name='user',
            email='test@gmail.com',
            password='testtest',
            search_url='test.com'
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual((u.experienced_owner), '1')
        self.assertEqual((u.kids), '2')
        self.assertEqual((u.dogs), '3')
        self.assertEqual((u.cats), '4')
        self.assertEqual((u.lifestyle), '5')
        self.assertEqual((u.home_type), '6')
        self.assertEqual((u.qualities), '{7,8,9}')
        self.assertEqual((u.zip_code), 12345)
        self.assertEqual((u.first_name), 'test')
        self.assertEqual((u.last_name), 'user')
        self.assertEqual((u.email), 'test@gmail.com')
        self.assertEqual((u.password), 'testtest')
        self.assertEqual((u.search_url), 'test.com')
    
    def test_user_authentication(self):
        """Does user authentication work?"""

        u = User.signup(
            experienced_owner='1',
            kids='2',
            dogs='3',
            cats='4',
            lifestyle='5',
            home_type='6',
            qualities=['7','8','9'],
            zip_code=12345,
            first_name='test',
            last_name='user',
            email='test@gmail.com',
            password='testtest',
            search_url='test.com'
        )

        db.session.add(u)
        db.session.commit()

        user = User.authenticate('test@gmail.com',
                                 'testtest')
        user2 = User.authenticate('tester@gmail.com',
                                 'testtest')
        user3 = User.authenticate('test@gmail.com',
                                 'testeetest')

        self.assertEqual(u, user)
        self.assertNotEqual(u, user2)
        self.assertNotEqual(u, user3)