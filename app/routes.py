"""Provides all routes for the Social Insecurity application.

This file contains the routes for the application. It is imported by the app package.
It also contains the SQL queries used for communicating with the database.
"""

from pathlib import Path

from flask import flash, redirect, render_template, send_from_directory, url_for, session, request

from app import app, sqlite, bcrypt
from app.forms import CommentsForm, FriendsForm, IndexForm, PostForm, ProfileForm
import os
import re
import bleach 
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, current_user, logout_user

@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    ###IDEA USE parameterized queries to prevent SQL injection,
    """Provides the index page for the application.

    It reads the composite IndexForm and based on which form was submitted,
    it either logs the user in or registers a new user.

    If no form was submitted, it simply renders the index page.
    """
    index_form = IndexForm()
    login_form = index_form.login
    register_form = index_form.register

    if login_form.is_submitted() and login_form.submit.data:
        if not re.match("^[a-zA-Z0-9_@]+$", index_form.login.username.data):
            flash_message = bleach.clean("Invalid Username")
            flash(flash_message)
            return render_template("index.html.j2", title="Welcome", form=index_form)

        query = "SELECT * FROM Users WHERE username = ?" ###https://stackoverflow.com/questions/6786034/can-parameterized-statement-stop-all-sql-injection
        user = sqlite.query(query, one=True, args=(index_form.login.username.data,))

        if user is None:
            flash("Sorry, this user does not exist!", category="warning")
        elif bcrypt.check_password_hash(user["password"], login_form.password.data) == True:
            session['username'] = user['username']
            return redirect(url_for("stream", username=index_form.login.username.data))
        else:
            flash("Sorry, wrong password!", category="warning")

    elif register_form.is_submitted() and register_form.submit.data and register_form.validate_on_submit():
        query = "SELECT username FROM Users WHERE username = ?"
        existing_user = sqlite.query(query, one=True, args=(register_form.username.data,))

        if existing_user:
            flash_message = bleach.clean("User already in use", tags=[], attributes={}) #<script>alert('XSS Attack');</script>
            flash(flash_message, category="success")
            return redirect(url_for('index'))
        #hash and verify passwords using the bcrypt hashing algorithm 
        user_password = register_form.password.data
        hashed_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        
        query = "INSERT INTO Users (username, first_name, last_name, password) VALUES (?, ?, ?, ?)"
        user_data = (register_form.username.data, register_form.first_name.data, register_form.last_name.data, hashed_password)
        sqlite.query(query, one=True, args=user_data)

        flash("User successfully created!", category="success")
        return redirect(url_for("index"))
    # else: 
    #     for field, errors in register_form.errors.items():
    #         for error in errors: 
    #             flash(f"Validation error for {field}: {error}", category="error")
    

    return render_template("index.html.j2", title="Welcome", form=index_form)



#if anyone tryes to access non-accessible page, send them to index
@app.before_request
def require_login(): ##THIS AT THE MOMENT ISNT WORKINGGG
    allowed_routes = ['index']
    if 'username' not in session and request.endpoint not in allowed_routes:
        flash("Please log in to access this page.", category="error")
        return redirect(url_for('index'))


   
@app.route("/stream/<string:username>", methods=["GET", "POST"])
#@login_required
def stream(username: str):
    """Provides the stream page for the application.

    If a form was submitted, it reads the form data and inserts a new post into the database.

    Otherwise, it reads the username from the URL and displays all posts from the user and their friends.
    """
    post_form = PostForm()
    get_user = "SELECT * FROM Users WHERE username = ?"
    user = sqlite.query(get_user, one=True, args=(username,))
    if post_form.is_submitted():
        if post_form.image.data:
            # Check the file size
            max_file_size = 10 * 1024 * 1024  
            if len(post_form.image.data.read()) > max_file_size:
                flash("File size exceeds allowed limit.", category="error")
                return redirect(url_for("stream", username=username))
            filename = secure_filename(post_form.image.data.filename)
            path = Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"] / filename
            post_form.image.data.save(path)

        insert_post_query = """
            INSERT INTO Posts (u_id, content, image, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
            """
        args = (user["id"], post_form.content.data, post_form.image.data.filename)
        sqlite.query(insert_post_query, args=args)
        return redirect(url_for("stream", username=username))
   
    get_posts_query = """
        SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id = p.id) AS cc
        FROM Posts AS p JOIN Users AS u ON u.id = p.u_id
        WHERE p.u_id IN (
            SELECT u_id FROM Friends WHERE f_id = ?
            ) OR p.u_id IN (
            SELECT f_id FROM Friends WHERE u_id = ?
            ) OR p.u_id = ?
            ORDER BY p.creation_time DESC;
        """
    args = (user["id"], user["id"], user["id"])
    posts = sqlite.query(get_posts_query, args=args)

    cleanedPosts = []
    
    for post in posts:
        cleanedPost = {}
        cleanedPost.update(post)
        cleanedPost["content"] = bleach.clean(post["content"])
        cleanedPosts.append(cleanedPost)
    
    return render_template("stream.html.j2", title="Stream", username=username, form=post_form, posts=posts)


@app.route("/comments/<string:username>/<int:post_id>", methods=["GET", "POST"])
def comments(username: str, post_id: int):
    """Provides the comments page for the application.

    If a form was submitted, it reads the form data and inserts a new comment into the database.

    Otherwise, it reads the username and post id from the URL and displays all comments for the post.
    """
    comments_form = CommentsForm()
    get_user = """
        SELECT *
        FROM Users
        WHERE username = ?;
    """
    user = sqlite.query(get_user, one=True, args=(username,))

    if comments_form.is_submitted():
        # Sanitize user comment data using bleach
        user_comment = bleach.clean(comments_form.comment.data, tags=[], attributes={})
        insert_comment = """
            INSERT INTO Comments (p_id, u_id, comment, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
        """
        sqlite.query(insert_comment, args=(post_id, user["id"], user_comment))

    get_post = """
        SELECT *
        FROM Posts AS p JOIN Users AS u ON p.u_id = u.id
        WHERE p.id = ?;
    """
    post = sqlite.query(get_post, one=True, args=(post_id,))
    
    get_comments = """
        SELECT DISTINCT *
        FROM Comments AS c JOIN Users AS u ON c.u_id = u.id
        WHERE c.p_id = ?
        ORDER BY c.creation_time DESC;
    """
    comments = sqlite.query(get_comments, args=(post_id,))
    
    # post = sqlite.query(get_post, one=True)
    # comments = sqlite.query(get_comments)
    return render_template(
        "comments.html.j2", title="Comments", username=username, form=comments_form, post=post, comments=comments
    )


@app.route("/friends/<string:username>", methods=["GET", "POST"])
def friends(username: str):
    """Provides the friends page for the application.

    If a form was submitted, it reads the form data and inserts a new friend into the database.

    Otherwise, it reads the username from the URL and displays all friends of the user.
    """
    friends_form = FriendsForm()
    
    get_user = """
        SELECT *
        FROM Users
        WHERE username = ?;
    """
    user = sqlite.query(get_user, one=True, args=(username,))

    if friends_form.is_submitted():
        # Fetch friend data using a parameterized query
        get_friend = """
            SELECT *
            FROM Users
            WHERE username = ?;
        """
        friend = sqlite.query(get_friend, one=True, args=(friends_form.username.data,))
        
        get_friends = """
            SELECT f_id
            FROM Friends
            WHERE u_id = ?;
        """
        friends = sqlite.query(get_friends, args=(user["id"],))

        if friend is None:
            flash("User does not exist!", category="warning")
        elif friend["id"] == user["id"]:
            flash("You cannot be friends with yourself!", category="warning")
        elif friend["id"] in [friend["f_id"] for friend in friends]:
            flash("You are already friends with this user!", category="warning")
        else:
            insert_friend = """
                INSERT INTO Friends (u_id, f_id)
                VALUES (?, ?);
            """
            sqlite.query(insert_friend, args=(user["id"], friend["id"]))
            flash("Friend successfully added!", category="success")

    get_friends = """
        SELECT *
        FROM Friends AS f JOIN Users as u ON f.f_id = u.id
        WHERE f.u_id = ? AND f.f_id != ?
        """
    friends = sqlite.query(get_friends, args=(user["id"], user["id"]))
    return render_template("friends.html.j2", title="Friends", username=username, friends=friends, form=friends_form)
@app.route("/profile/<string:username>", methods=["GET", "POST"])
def profile(username: str):
    """Provides the profile page for the application.

    If a form was submitted, it reads the form data and updates the user's profile in the database.

    Otherwise, it reads the username from the URL and displays the user's profile.
    """
    profile_form = ProfileForm()
    get_user = """
        SELECT *
        FROM Users
        WHERE username = ?;
    """
    user = sqlite.query(get_user, one=True, args=(username,))

    if profile_form.is_submitted() and profile_form.validate_on_submit():
        update_profile = """
            UPDATE Users
            SET education=?, employment=?, music=?, movie=?, nationality=?, birthday=?
            WHERE username=?;
        """
        sqlite.query(update_profile, args=(
            profile_form.education.data,
            profile_form.employment.data,
            profile_form.music.data,
            profile_form.movie.data,
            profile_form.nationality.data,
            profile_form.birthday.data,
            username
        ))
        return redirect(url_for("profile", username=username))

    user_data = dict(user)  # Convert SQLite Row to a dictionary
    user_data["education"] = bleach.clean(user_data["education"])
    user_data["employment"] = bleach.clean(user_data["employment"])
    user_data["music"] = bleach.clean(user_data["music"])
    user_data["movie"] = bleach.clean(user_data["movie"])
    user_data["nationality"] = bleach.clean(user_data["nationality"])
    user_data["birthday"] = bleach.clean(user_data["birthday"])

    # Pre-fill the profile form with user data
    profile_form.process(obj=user_data)

    return render_template("profile.html.j2", title="Profile", username=username, user=user, form=profile_form)



@app.route("/uploads/<string:filename>")
def uploads(filename):
    """Provides an endpoint for serving uploaded files."""
    return send_from_directory(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"], filename)
