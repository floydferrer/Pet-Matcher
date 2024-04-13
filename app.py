from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, json
from flask_debugtoolbar import DebugToolbarExtension
from flask_bcrypt import Bcrypt
import requests, itertools
from sqlalchemy.exc import IntegrityError
from forms import MatchForm, NewAccountForm, LoginForm
from models import db, connect_db, User, Tag

client_id = 'kK4MSKCnl6f8CT0w7qPg9c9VfwfOFPfdQe8CUcPfxWLxMbvQXI'
client_secret = 'D31cBJy3f7LMBCU8tgyNMqoNlmmG3JdD1Hhn4ZhA'
grant_type = 'client_credentials'

API_BASE_URL = 'https://api.petfinder.com/v2/animals'

results = []
search_params = ''

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pet_matcher'

app.app_context().push()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "it's a secret"
toolbar = DebugToolbarExtension(app)

connect_db(app)
bcrypt = Bcrypt()

def get_access_token(client_id, client_secret):
    """Generate new access token"""
    
    headers = {'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': grant_type}
    t = requests.post(f'https://api.petfinder.com/v2/oauth2/token', json=headers)
    token = t.json()
    return f"Bearer {token['access_token']}"

authorization = get_access_token(client_id, client_secret)

def do_login(user):
    """Log in user"""

    session['CURRUSER'] = user.id
    if 'PARAMS' in session:
        del session['PARAMS']
    if 'RECOMMENDED_PETS' in session:
        del session['RECOMMENDED_PETS']
    if 'UPDATEFORM' in session:
        del session['UPDATEFORM']

def do_logout():
    """Logout user and clear session variables"""

    if 'CURRUSER' in session:
        del session['CURRUSER']
    if 'PARAMS' in session:
        del session['PARAMS']
    if 'RECOMMENDED_PETS' in session:
        del session['RECOMMENDED_PETS']
    if 'UPDATEFORM' in session:
        del session['UPDATEFORM']


def submit_quiz(quiz_form):
    """Handle pet quiz submission"""
    
    if 'CURRUSER' in session:
        # Allows logged in user's to update quiz results instead of loading previously stored search parameters 
        session['UPDATEFORM'] = True
    
    results = get_results(quiz_form)
    pet_scores = save_results(results, quiz_form)
    
    # When returning to Recommended Pets page, allows recommended pets to display without sending new request to API
    session['RECOMMENDED_PETS'] = rank_pets(pet_scores, results)
    
    # Since new account creation is optional after quiz is completed created, Search parameters are stored in session to complete new account creation
    session['PARAMS'] = {
        'experienced_owner': quiz_form.experienced_owner.data, 
        'kids': quiz_form.kids.data, 
        'dogs': quiz_form.dogs.data, 
        'cats': quiz_form.cats.data, 
        'lifestyle': quiz_form.lifestyle.data, 
        'home_type': quiz_form.home_type.data, 
        'qualities': list(quiz_form.qualities.data), 
        'zip_code': quiz_form.zip_code.data, 
        'search_url': search_params
    }
    
    if 'CURRUSER' in session:
        user = User.query.get(session['CURRUSER'])
        user.search_url = session['PARAMS']['search_url']
        db.session.add(user)
        db.session.commit()
        flash(f'Recommended pets have been updated', 'success')           

def get_results(val):
    """Retrieve pet results filtered by quiz answers"""
    
    headers = {'Authorization': authorization}
    current_page = 1
    results = []
    global search_params
    
    # Set search parameters for new quiz submissions (new users) or updating search parameters for updated quiz submissions (current users)
    if 'CURRUSER' not in session or ('CURRUSER' in session and 'UPDATEFORM' in session):
        params = f'location={val.zip_code.data}&distance=25&limit=100&status=adoptable'
        if val.pet_type.data == 'dog':
            params += '&type=dog'
        if val.pet_type.data == 'cat':
            params += '&type=cat'
        if val.kids.data == 'kidshouse':
            params += '&good_with_children=true'
        if val.dogs.data == 'doghouse':
            params += '&good_with_dogs=true'
        if val.cats.data == 'cathouse':
            params += '&good_with_cats=true'
    else:
        user = User.query.get_or_404(val)
        params = f'location={user.zip_code}&distance=25&limit=100&status=adoptable{user.search_url}'
    search_params = params
    r = requests.get(f'{API_BASE_URL}?{params}&page=1', headers=headers)
    res = r.json()
    page_count = res['pagination']['total_pages']
    for animal in res['animals']:
        results.append(animal)
    current_page += 1
    while current_page <= page_count:
        r = requests.get(f'{API_BASE_URL}?{params}&page={current_page}', headers=headers)
        res = r.json()
        for animal in res['animals']:
            results.append(animal)
        current_page += 1
    return results

def save_results(results, val):
    """Scores all pets within pet results"""
   
    pet_scores = {}
    for animal in results:
        if bool(animal['photos']) == False:
            animal['score'] = -1
        else:
            animal['score'] = 0
            for tag in animal['tags']:
                t = Tag.query.filter(Tag.tag_name == tag).first()
                if t != None:
                    # Pet Scoring for new users/current users retaking quiz (takes in form data) or current users logging in (takes in user data)
                    if 'CURRUSER' not in session or ('CURRUSER' in session and 'UPDATEFORM' in session):
                        if t.pet_owner == val.experienced_owner.data:
                            animal['score'] += 1
                        if t.lifestyle == val.lifestyle.data:
                            animal['score'] += 1
                        if t.home_size == val.home_type.data:
                            animal['score'] += 1
                        if t.qualities != None:
                            if t.qualities in val.qualities.data:
                                animal['score'] += 1
                    else:
                        if t.pet_owner == val.experienced_owner:
                            animal['score'] += 1
                        if t.lifestyle == val.lifestyle:
                            animal['score'] += 1
                        if t.home_size == val.home_type:
                            animal['score'] += 1
                        if t.qualities != None:
                            if t.qualities in val.qualities:
                                animal['score'] += 1
        pet_scores[animal['id']] = animal['score']  
        print(f"Name: {animal['name']}")
        print(f"Pet ID: {animal['id']}")
        print(f"Tag Score: {animal['score']}")
    return pet_scores

def rank_pets(pet_scores, results):
    """Ranks pet scores in descending order, limit 10"""
    
    sorted_pet_scores = sorted(pet_scores.items(), key=lambda x:x[1], reverse=True)
    sorted_pet_scores_dict = dict(sorted_pet_scores)
    top_pet_scores = dict(itertools.islice(sorted_pet_scores_dict.items(), 10))
    top_pet_ids = list(top_pet_scores.keys())

    recommended_pet = {}
    pet_counter = 0
    for pet_id in top_pet_ids:
        pet = list(filter(lambda x:x['id']==pet_id, results))[0]
        recommended_pet[pet_counter] = {
            'petfinder_id': pet['id'],
            'name': pet['name'],
            'breed': pet['breeds']['primary'],
            'age': pet['age'],
            'gender': pet['gender'],
            'photo': pet['primary_photo_cropped']['medium'] if pet['primary_photo_cropped'] != None else pet['photos'][0]['medium'],
            'zip_code': pet['contact']['address']['postcode'],
            'tag': pet['tags'],
            'url' : pet['url']
        }
        pet_counter += 1
    print(f'Top Pet Scores: {top_pet_scores}')
    print(f'Top Pet IDs: {top_pet_ids}')
    return recommended_pet

def create_user(user_form):
    """Create new user and save search parameters to user account"""
    
    hashed_pwd = bcrypt.generate_password_hash(user_form.password.data).decode('UTF-8')
    new_user = User(
        experienced_owner = session['PARAMS']['experienced_owner'], 
        kids = session['PARAMS']['kids'], 
        dogs = session['PARAMS']['dogs'], 
        cats = session['PARAMS']['cats'], 
        lifestyle = session['PARAMS']['lifestyle'], 
        home_type = session['PARAMS']['home_type'], 
        qualities = session['PARAMS']['qualities'], 
        zip_code = session['PARAMS']['zip_code'], 
        search_url = session['PARAMS']['search_url'],
        first_name = user_form.first_name.data,
        last_name = user_form.last_name.data,
        email = user_form.email.data,
        password = hashed_pwd
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

### App Routes ###
@app.route('/', methods=['GET', 'POST'])
def show_homepage():
    """Render Pet Quiz page"""
    
    global recommended_pet
    global results
    form = MatchForm()
    if form.validate_on_submit():
        if len(form.qualities.data) < 4:
            submit_quiz(form)
            return redirect('/results')
        else:
            flash('Pick no more than 3 qualities!')
            return render_template('homepage.html', form=form)
    return render_template('homepage.html', form=form)

@app.route('/results')
def display_pet_results():
    """Display pet results after login or updated pet results after logged in user submits new pet quiz"""
    
    global recommended_pet
    if 'CURRUSER' in session and 'RECOMMENDED_PETS' not in session:
        user = User.query.get(session['CURRUSER'])
        results = get_results(user.id)
        pet_scores = save_results(results, user)
        session['RECOMMENDED_PETS'] = rank_pets(pet_scores, results)
    elif 'CURRUSER' in session and 'RECOMMENDED_PETS' in session and 'PARAMS' in session:
        user = User.query.get(session['CURRUSER'])
        user.experienced_owner = session['PARAMS']['experienced_owner']
        user.kids = session['PARAMS']['kids']
        user.dogs = session['PARAMS']['dogs']
        user.cats = session['PARAMS']['cats']
        user.lifestyle = session['PARAMS']['lifestyle']
        user.home_type = session['PARAMS']['home_type']
        user.qualities = session['PARAMS']['qualities']
        user.zip_code = session['PARAMS']['zip_code']
        user.search_url = session['PARAMS']['search_url']
        db.session.add(user)
        db.session.commit()
    # Prevent new account creation before pet quiz is completed
    elif 'CURRUSER' not in session and 'PARAMS' not in session:
        flash(f'Please complete quiz first!', 'warning')
        return redirect('/')

    return render_template('pet-results.html', pets=session['RECOMMENDED_PETS'])

@app.route('/signup', methods=['GET', 'POST'])
def add_user():
    """Handle new user signup"""
    
    form = NewAccountForm()
    if form.validate_on_submit():
        if 'PARAMS' in session:
            new_user = create_user(form)
            session['CURRUSER'] = new_user.id
            flash(f'User has been created', 'success')
            return redirect('/results')
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Handle user login"""
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Welcome back, {user.first_name}!", "success")
            return redirect("/results")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """Handle logout of user"""
    
    do_logout()
    flash('Successfully logged out!', 'success')
    return redirect('/login')