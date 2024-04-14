from flask import Flask, render_template, request, flash, redirect, session, json
from flask_debugtoolbar import DebugToolbarExtension
from flask_bcrypt import Bcrypt
import requests, itertools
from sqlalchemy.exc import IntegrityError
from forms import MatchForm1, MatchForm2, MatchForm3, MatchForm4, MatchForm5, MatchForm6, MatchForm7, MatchForm8, MatchForm9, NewAccountForm, LoginForm
from models import db, connect_db, User, Tag

client_id = 'kK4MSKCnl6f8CT0w7qPg9c9VfwfOFPfdQe8CUcPfxWLxMbvQXI'
client_secret = 'D31cBJy3f7LMBCU8tgyNMqoNlmmG3JdD1Hhn4ZhA'
grant_type = 'client_credentials'

API_BASE_URL = 'https://api.petfinder.com/v2/animals'

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
    if 'responses' in session:
        del session['responses']

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
    if 'responses' in session:
        del session['responses']


def submit_quiz(quiz_form):
    """Handle pet quiz submission"""
    
    if 'CURRUSER' in session:
        # Allows logged in user's to update quiz results instead of loading previously stored search parameters 
        session['UPDATEFORM'] = True
    
    results = get_results(quiz_form)
    pet_scores = save_results(results, quiz_form)
    
    # When returning to Recommended Pets page, allows recommended pets to display without sending new request to API
    session['RECOMMENDED_PETS'] = rank_pets(pet_scores, results)
    
    if 'CURRUSER' in session:
        user = User.query.get(session['CURRUSER'])
        user.search_url = session['PARAMS']['search_url']
        db.session.add(user)
        db.session.commit()
        flash(f'Recommended pets have been updated')           

def get_results(val):
    """Retrieve pet results filtered by quiz answers"""
    
    headers = {'Authorization': authorization}
    current_page = 1
    results = []
    
    # Set search parameters for new quiz submissions (new users) or updating search parameters for updated quiz submissions (current users)
    if 'CURRUSER' not in session or ('CURRUSER' in session and 'UPDATEFORM' in session):
        params = f'location={session["responses"][8]}&distance=25&limit=100&status=adoptable'
        if session['responses'][1] == 'dog':
            params += '&type=dog'
        if session['responses'][1] == 'cat':
            params += '&type=cat'
        if session['responses'][2] == 'kidshouse':
            params += '&good_with_children=true'
        if session['responses'][3] == 'doghouse':
            params += '&good_with_dogs=true'
        if session['responses'][4] == 'cathouse':
            params += '&good_with_cats=true'
        
        # Since new account creation is optional after quiz is completed created, Search parameters are stored in session to complete new account creation
        session['PARAMS'] = {
            'experienced_owner': session['responses'][0], 
            'kids': session['responses'][2], 
            'dogs': session['responses'][3], 
            'cats': session['responses'][4], 
            'lifestyle': session['responses'][5], 
            'qualities': session['responses'][6],
            'home_type': session['responses'][7],             
            'zip_code': session['responses'][8], 
            'search_url': params
        }
    else:
        user = User.query.get_or_404(val)
        params = f'location={user.zip_code}&distance=25&limit=100&status=adoptable{user.search_url}'
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
                        if t.pet_owner == session['responses'][0]:
                            animal['score'] += 1
                        if t.lifestyle == session['responses'][5]:
                            animal['score'] += 1
                        if t.qualities != None:
                            if t.qualities in session['responses'][6]:
                                animal['score'] += 1
                        if t.home_size == session['responses'][7]:
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
    """Pet Quiz Prompt Page"""

    return render_template('homepage.html')

@app.route('/results')
def display_pet_results():
    """Display pet results after login or updated pet results after logged in user submits new pet quiz"""
    # if 'responses' in session:
    #     if len(session['responses']) == 9 and 'RECOMMENDED_PETS' not in session:
    #         submit_quiz(session['responses'])
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
    elif 'CURRUSER' not in session and 'responses' not in session:
        flash(f'Please complete quiz first!')
        return redirect('/')

    return render_template('pet-results.html', pets=session['RECOMMENDED_PETS'])
    
@app.route('/success')
def confirm_login():
    if 'CURRUSER' in session and 'PARAMS' not in session and 'RECOMMENDED_PETS' not in session and 'UPDATEFORM' not in session and 'responses' not in session:
        user = User.query.get(session['CURRUSER'])
        flash(f'Welcome back, {user.first_name}!')
        return render_template('login-success.html')
    if 'CURRUSER' in session:
        flash(f'Already logged in!')
    else:
        flash(f'Please login first!')
    return redirect('/login')
    
@app.route('/form-complete')
def handle_form_completion():
    if len(session['responses']) == 9:
        return render_template('form-complete.html')
    flash(f'Please complete quiz!')
    return redirect('/')

@app.route('/submit')
def handle_form_submission():
    submit_quiz(session['responses'])
    return redirect('/results')

@app.route('/signup', methods=['GET', 'POST'])
def add_user():
    """Handle new user signup"""
    
    form = NewAccountForm()
    if form.validate_on_submit():
        if 'PARAMS' in session:
            new_user = create_user(form)
            session['CURRUSER'] = new_user.id
            flash(f'User has been created')
            return redirect('/results')
        # ADD CODE HERE: Prevent new account creation before pet quiz is completed
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
            return redirect('/success')

        flash("Invalid credentials.")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """Handle logout of user"""
    
    do_logout()
    flash('Successfully logged out!')
    return redirect('/login')

@app.route('/reset', methods=['POST'])
def reset_responses():
    session['responses'] = []
    return redirect('/questions/0')

question_forms = ['MatchForm1', 'MatchForm2', 'MatchForm3', 'MatchForm4', 'MatchForm5', 'MatchForm6', 'MatchForm7', 'MatchForm8', 'MatchForm9']
question_labels = ['experienced_owner', 'pet_type', 'kids', 'dogs', 'cats', 'lifestyle', 'qualities', 'home_type', 'zip_code']

@app.route('/questions/<int:q>', methods=['GET', 'POST'])
def show_question(q):
    form = globals()[question_forms[q]]()
    if form.validate_on_submit():
        if form[question_labels[q]].label.field_id == 'qualities':
            if len(form[question_labels[q]].data) >= 4:
                flash('Pick no more than 3 qualities!')
                return render_template(f'questions/{q}.html', q=int(q)+1, form=form, question_labels=question_labels)
        responses = session['responses']
        responses.append(form[question_labels[q]].data)
        session['responses'] = responses
        if q == 8:
            return redirect('/form-complete')
        return redirect(f'/questions/{q+1}')
    while int(q) < len(session['responses']):
        responses = session['responses']
        responses.pop()
        session['responses'] = responses
    if (len(session['responses']) < int(q)):
        flash('Please complete current question!')
        return redirect(f'/questions/{len(session["responses"])}')
    return render_template(f'questions/{q}.html', q=int(q)+1, form=form, question_labels=question_labels)
