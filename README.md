# Pet Matcher App

Application was created to help both first time pet owners and current owners get matched up with pets (Dogs or Cats) that fit their lifestyle and home needs

## API: Petfinder (https://www.petfinder.com/developers/v2/docs/)

## Tech Stacks: Python, HTML, CSS, Flask, WTForms

## Features

1. Pet Quiz (9 questions). Can be retaken to generate new matches. Questions consist of:
  - Owner Type
  - Pet preference
  - Kids at home
  - Cats/Dogs at home
  - Lifestyle type
  - Ideal Pet Qualities
  - Home Size
  - Location
3. Account creation to save quiz parameters
4. Link Click Out driving to corresponding pet details page on Petfinder.com

## User Flow

### New Users
1. Quiz intro page
2. Quiz (9 separated questions)
3. Pet Results
4. Pet Detail Page on Petfinder.com, Account Creation or Retake Quiz

### Existing Users
1. Quiz intro page
2. Account Login Page
3. Pet Results

## Tags
All available tags from API were evaluated and, where appropriate, given a designation that corresponds with the designations given to all possible quiz answers ('Active dog' tag would match to 'Active' lifestyle answer, etc.). To maximize efficiency of POST request, all API tags (and designations) are seeded to the Tags table (Pet_Matcher_Tags.csv) within the pet-matcher db to prevent an additional tag request call to API.

## Quiz Submission POST request details
1. User submits quiz via POST request to API
2. API responds with full pet list of all pets within a 25 mile radius of submitted location that meet the parameter criteria from user's quiz answers
3. Tags of each pet is cross-referenced to all tags that correspond with user's quiz answers, and a score of +1 is given to that pet for each tag match
4. Pets are ranked by total score and the top 10 highest scoring pets are added to session['RECOMMENDEDPETS']
5. Top 10 pets are displayed in Pet Recommendation page via session['RECOMMENDEDPETS']
