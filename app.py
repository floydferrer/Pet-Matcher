from flask import Flask, render_template, request, flash, redirect, session, g, jsonify, json
from flask_debugtoolbar import DebugToolbarExtension
from flask_bcrypt import Bcrypt
import requests, itertools
from sqlalchemy.exc import IntegrityError
from forms import MatchForm, NewAccountForm, LoginForm
from models import db, connect_db, User, Pet, Tag

client_id = 'kK4MSKCnl6f8CT0w7qPg9c9VfwfOFPfdQe8CUcPfxWLxMbvQXI'
client_secret = 'D31cBJy3f7LMBCU8tgyNMqoNlmmG3JdD1Hhn4ZhA'
grant_type = 'client_credentials'

API_BASE_URL = 'https://api.petfinder.com/v2/animals'

# recommended_pet = {}
results = []
search_params = ''


# NEED TO RETURN RESULTS FROM ALL PAGES (CURRENTLY RETURNING 1ST PAGE ONLY). LOOK INTO PAGINATION

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

# Get access token
def get_access_token(client_id, client_secret):
    headers = {'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': grant_type}
    t = requests.post(f'https://api.petfinder.com/v2/oauth2/token', json=headers)
    token = t.json()
    return f"Bearer {token['access_token']}"

authorization = get_access_token(client_id, client_secret)

def do_login(user):
    """Log in user."""

    session['CURRUSER'] = user.id

def do_logout():
    """Logout user."""

    if 'CURRUSER' in session:
        del session['CURRUSER']
    if 'PARAMS' in session:
        del session['PARAMS']
    if 'RECOMMENDED_PETS' in session:
        del session['RECOMMENDED_PETS']
    if 'UPDATEFORM' in session:
        del session['UPDATEFORM']

# def submit_request(form):
#     headers = {'Authorization': authorization}
#     current_page = 1
#     results = []
    
#     params = f'location=90712&distance=25&limit=100&status=adoptable' # add adoptable as additional parameter
#     if form.pet_type.data == 'dog':
#         params += '&type=dog'
#     if form.pet_type.data == 'cat':
#         params += '&type=cat'
#     if form.kids.data == 'kidshouse':
#         params += '&good_with_children=true'
#     if form.dogs.data == 'doghouse':
#         params += '&good_with_dogs=true'
#     if form.cats.data == 'cathouse':
#         params += '&good_with_cats=true'
#     r = requests.get(f'{API_BASE_URL}?{params}&page=1', headers=headers)
#     res = r.json()
#     page_count = res['pagination']['total_pages']
#     for animal in res['animals']:
#         results.append(animal)
#     current_page += 1
#     while current_page <= page_count:
#         r = requests.get(f'{API_BASE_URL}?{params}&page={current_page}', headers=headers)
#         res = r.json()
#         for animal in res['animals']:
#             results.append(animal)
#         current_page += 1
#     return results

# Filtering out Tag names
def get_results(val):
    headers = {'Authorization': authorization}
    current_page = 1
    results = []
    global search_params
    
    params = f'location=90712&distance=25&limit=100&status=adoptable' # add adoptable as additional parameter
    if 'CURRUSER' not in session or ('CURRUSER' in session and 'UPDATEFORM' in session):
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
        params = user.search_url
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
    pet_scores = {}
    for animal in results:
        if bool(animal['photos']) == False:
            animal['score'] = -1
        else:
            animal['score'] = 0
            for tag in animal['tags']:
                t = Tag.query.filter(Tag.tag_name == tag).first()
                if t != None:
                    if 'CURRUSER' not in session:
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

# page_count = res['pagination']['total_pages']

# while current_page <= page_count:
#     r = requests.get(f'https://api.petfinder.com/v2/animals?type=dog&location=90712&distance=25&limit=100&page={page_counter}', headers=headers)
#     res = r.json()
#     for animal in res['animals']:
#         pets[pet_counter] = animal['tags']
#         pet_counter += 1

#     for pet in pets.values():
#         tags.append(pet) 

#     for tag in tags:
#         for t in tag:
#             tag_list.append(t)
#     current_page += 1
# tag_set = set(tag_list)

# tag_set = set(tags)


@app.route('/', methods=['GET', 'POST'])
def show_homepage():
    global recommended_pet
    global results
    form = MatchForm()
    if form.validate_on_submit():
        if len(form.qualities.data) < 4:
            if 'CURRUSER' in session:
                session['UPDATEFORM'] = True
            results = get_results(form)
            pet_scores = save_results(results, form)
            session['RECOMMENDED_PETS'] = rank_pets(pet_scores, results)
            # new_user = User(
            #     experienced_owner = form.experienced_owner.data, 
            #     kids = form.kids.data, 
            #     dogs = form.dogs.data, 
            #     cats = form.cats.data, 
            #     lifestyle = form.lifestyle.data, 
            #     home_type = form.home_type.data, 
            #     qualities = list(form.qualities.data), 
            #     zip_code = form.zip_code.data, 
            #     search_url = search_params
            #     )
            # db.session.add(new_user)
            # db.session.commit()
            session['PARAMS'] = {
                'experienced_owner': form.experienced_owner.data, 
                'kids': form.kids.data, 
                'dogs': form.dogs.data, 
                'cats': form.cats.data, 
                'lifestyle': form.lifestyle.data, 
                'home_type': form.home_type.data, 
                'qualities': list(form.qualities.data), 
                'zip_code': form.zip_code.data, 
                'search_url': search_params
            }
            if 'CURRUSER' in session:
                user = User.query.get(session['CURRUSER'])
                user.search_url = session['PARAMS']['search_url']
                db.session.add(user)
                db.session.commit()
                flash(f'Recommended pets have been updated', 'success')
            # u = User.query.get_or_404(new_user.id)
            # for pet in u.recommended_pet:
                # print(f'Pet: {pet}')
            
            # session['CURRUSER'] = new_user.id
            return redirect('/results')
            # print(f'{form.first_pet_owner.data} {form.pet_type.data} {form.children.data} {form.dogs.data} {form.cats.data} {form.lifestyle.data} {form.qualities.data} {form.home_type.data} {form.zipcode.data}')
        else:
            flash('Pick no more than 3 qualities!')
            return render_template('homepage.html', form=form)
    return render_template('homepage.html', form=form)

@app.route('/results')
def display_pet_results():
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
    elif 'CURRUSER' not in session and 'PARAMS' not in session:
        flash(f'Please complete quiz first!', 'warning')
        return redirect('/')

    return render_template('pet-results.html', pets=session['RECOMMENDED_PETS'])


@app.route('/signup', methods=['GET', 'POST'])
def add_user():
    form = NewAccountForm()
    
    if form.validate_on_submit():
        if 'PARAMS' in session:
            hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('UTF-8')
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
                first_name = form.first_name.data,
                last_name = form.last_name.data,
                email = form.email.data,
                password = hashed_pwd
            )
            db.session.add(new_user)
            db.session.commit()
            session['CURRUSER'] = new_user.id
            flash(f'User has been created', 'success')
            return redirect('/results')
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Handle user login."""

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
    """Handle logout of user."""

    do_logout()
    flash('Successfully logged out!', 'success')
    return redirect('/login') 