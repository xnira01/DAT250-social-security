"""Provides all forms used in the Social Insecurity application.

This file is used to define all forms used in the application.
It is imported by the app package.

Example:
    from flask import Flask
    from app.forms import LoginForm

    app = Flask(__name__)

    # Use the form
    form = LoginForm()
    if form.validate_on_submit() and form.login.submit.data:
        username = form.username.data
    """

from datetime import datetime
from typing import cast

from flask_wtf import FlaskForm
import re

from flask_wtf.file import FileAllowed

from wtforms import (
    BooleanField,
    DateField,
    FileField,
    FormField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,  
)
from wtforms.validators import DataRequired, Length, Regexp, ValidationError


# Defines all forms in the application, these will be instantiated by the template,
# and the routes.py will read the values of the fields

# Student(Done): Add validation, maybe use wtforms.validators??
from wtforms.validators import ValidationError, DataRequired, EqualTo, \
    Length

# TODO: There was some important security feature that wtforms provides, but I don't remember what; implement it


def Check_specialChr_and_number(form, field):
    word = field.data
    if not re.match("^[a-zA-Z0-9_@]+$", word):
        raise ValidationError('password must contain special characters')
    if not any(char.isdigit() for char in word):
        raise ValidationError('Password must contain at least one number.')
    
def check_upper(form, field):
    x = 0
    for element in field.data:
        if element.isupper() == True:
            x += 1
        
    if x == 0:
        raise ValidationError('Password need at least one upper case letter.')
    
def checkLowerCase(form, field):
    x = 0
    for element in field.data:
        if element.islower() == True:
            x += 1
        
    if x == 0:
        raise ValidationError('Password need at least one lower case letter.')

    
def NameValidator(form, field):
    username = field.data

    if any(char.isdigit() for char in username):
        raise ValidationError('A username should not contain numbers.')
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', username):
        raise ValidationError('A username should not contain special characters.')



class LoginForm(FlaskForm):
    """Provides the login form for the application."""

    username = StringField(label="Username", render_kw={"placeholder": "Username"},  validators=[DataRequired()])
    password = PasswordField(label="Password", render_kw={"placeholder": "Password"}, validators=[DataRequired()])
    remember_me = BooleanField(
        label="Remember me"
    )  # Done(student): It would be nice to have this feature implemented, probably by using cookies
    submit = SubmitField(label="Sign In")


class RegisterForm(FlaskForm):
    """Provides the registration form for the application."""

    first_name = StringField(
        label="First Name",
        render_kw={"placeholder": "First Name"},
        validators=[DataRequired(message = "First Name is required."), Length(min=4, max=15)]
    )
    last_name = StringField(
        label="Last Name",
        render_kw={"placeholder": "Last Name"},
        validators=[DataRequired(message="Last Name is required."), Length(min=4, max=15)]
    )
    username = StringField(
        label="Username",
        render_kw={"placeholder": "Username"},
        validators=[
            DataRequired(message="This field is required."),
            Length(min=5, message="Username must be at least 5 characters."),
            Regexp(r"^\w+$", message="Username must contain only letters, numbers, and underscores"),
            NameValidator
        ]
    )
    password = PasswordField(
        label="Password",
        validators=[DataRequired(message="This field is required."), Length(min=8, message="Password must be at least 8 characters."), Check_specialChr_and_number, checkLowerCase, check_upper],
        render_kw={"placeholder": "Password"}
    )
    confirm_password = PasswordField(
        label="Confirm Password",
        render_kw={"placeholder": "Confirm Password"},
        validators=[DataRequired(message="Passwords must match"), EqualTo('password')]
    )
    submit = SubmitField(label="Sign Up")

    def validate_username(self, username):
        # Add custom validation for the username if needed
        pass
       

class IndexForm(FlaskForm):
    """Provides the composite form for the index page."""

    login = cast(LoginForm, FormField(LoginForm))
    register = cast(RegisterForm, FormField(RegisterForm))


class PostForm(FlaskForm):
    """Provides the post form for the application."""

    content = TextAreaField(label="New Post", render_kw={"placeholder": "What are you thinking about?"})
    image = FileField('Image', 
                      validators=[FileAllowed(['jpg', 'png', 'img', 'jpeg', 'data'], 
                                              'Only jpeg, jpg, png and img files are allowed')]) #type validation
    submit = SubmitField(label="Post")


class CommentsForm(FlaskForm):
    """Provides the comment form for the application."""

    comment = TextAreaField(label="New Comment", render_kw={"placeholder": "What do you have to say?"})
    submit = SubmitField(label="Comment")


class FriendsForm(FlaskForm):
    """Provides the friend form for the application."""

    username = StringField(label="Friend's username", render_kw={"placeholder": "Username"})
    submit = SubmitField(label="Add Friend")


class ProfileForm(FlaskForm):
    """Provides the profile form for the application."""

    education = StringField(label="Education", render_kw={"placeholder": "Highest education"})
    employment = StringField(label="Employment", render_kw={"placeholder": "Current employment"})
    music = StringField(label="Favorite song", render_kw={"placeholder": "Favorite song"})
    movie = StringField(label="Favorite movie", render_kw={"placeholder": "Favorite movie"})
    nationality = StringField(label="Nationality", render_kw={"placeholder": "Your nationality"})
    birthday = DateField(label="Birthday", default=datetime.now())
    submit = SubmitField(label="Update Profile")
