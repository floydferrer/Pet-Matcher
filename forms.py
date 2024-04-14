from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, PasswordField, RadioField, SelectMultipleField, IntegerField, ValidationError, widgets
from wtforms.validators import DataRequired, Email, Length


class SelectMultipleFieldWithCheckboxes(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MatchForm1(FlaskForm):
    """Form for pet matching questionnaire"""

    experienced_owner = RadioField('Are you a first time pet owner?', choices=[('firstowner', 'Yes'), ('currentowner', 'No')], coerce=str, validators=[DataRequired()])

class MatchForm2(FlaskForm):
    """Form for pet matching questionnaire"""

    pet_type = RadioField('What type of pet are you interested in adopting?', choices=[('dog', 'Dog'), ('cat', 'Cat')], coerce=str, validators=[DataRequired()])

class MatchForm3(FlaskForm):
    """Form for pet matching questionnaire"""

    kids = RadioField('Are there any children in your household?', choices=[('kidshouse', 'Yes'), ('nokidshouse', 'No')], coerce=str, validators=[DataRequired()])

class MatchForm4(FlaskForm):
    """Form for pet matching questionnaire"""

    dogs = RadioField('Are there any dogs in your household?', choices=[('doghouse', 'Yes'), ('nodoghouse', 'No')], coerce=str, validators=[DataRequired()])

class MatchForm5(FlaskForm):
    """Form for pet matching questionnaire"""

    cats = RadioField('Are there any cats in your household?', choices=[('cathouse', 'Yes'), ('nocathouse', 'No')], coerce=str, validators=[DataRequired()])

class MatchForm6(FlaskForm):
    """Form for pet matching questionnaire"""

    lifestyle = RadioField('Describe your lifestyle', choices=[('active', 'Active'), ('laidback', 'Laidback')], coerce=str, validators=[DataRequired()])

class MatchForm7(FlaskForm):
    """Form for pet matching questionnaire"""

    qualities = SelectMultipleFieldWithCheckboxes('Pick up to 3 pet qualities', choices=[('loyal', 'Loyal'), ('protective', 'Protective'), ('loving', 'Loving'), ('obedient', 'Obedient'), ('playful', 'Playful')], coerce=str)

class MatchForm8(FlaskForm):
    """Form for pet matching questionnaire"""

    home_type = RadioField('Describe your home size', choices=[('small', 'Small'), ('large', 'Medium'),  ('large', 'Large')], coerce=str, validators=[DataRequired()])

class MatchForm9(FlaskForm):
    """Form for pet matching questionnaire"""

    zip_code = IntegerField('What is your zip code?', validators=[DataRequired()])

class NewAccountForm(FlaskForm):
    """Form for creating new account"""

    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class LoginForm(FlaskForm):
    """Form for creating new account"""

    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])