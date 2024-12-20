from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm
from forms import CreatePostForm
from forms import LoginForm
from forms import CommentForm
from bs4 import BeautifulSoup
import lxml
import os


'''
Make sure the required packages are installed:
Open the Terminal in PyCharm (bottom left).

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('key')
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship('User', back_populates='posts')

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    facility: Mapped[str] = mapped_column(String(250), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)

    comment = relationship('Comment', back_populates='post')


# TODO: Create a User table for all your registered users.
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    posts = relationship('BlogPost', back_populates='author')
    comment = relationship('Comment', back_populates='writer')


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    writer_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    writer = relationship('User', back_populates='comment')

    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    post = relationship('BlogPost', back_populates='comment')


with app.app_context():
    db.create_all()


# def admin_only(function):
#     @wraps(function)
#     # When @wraps is used, it copies over attributes such as __name__, __doc__,
#     # and others from the original function to the wrapper function.
#     # If you're sure that the metadata preservation isn't important for your use case,
#     # removing @wraps might not have significant consequences.
#     def decorated_function(*args, **kwargs):
#         # If id is not 1 then return abort with 403 error
#         if current_user.id != 1:
#             return abort(403)
#         # Otherwise continue with the route function
#         return function(*args, **kwargs)
#     return decorated_function


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        email_in_db = db.session.execute(db.select(User).where(User.email == email)).scalar()

        password = request.form.get("password")
        hashed_and_salted_password = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)

        if email_in_db:
            flash("Your email already exists.")
            return redirect(url_for('register'))

        else:
            new_user = User(
                email=request.form.get("email"),
                password=hashed_and_salted_password,
                name=request.form.get("name")
            )
            db.session.add(new_user)
            db.session.commit()
            result = db.session.execute(db.select(BlogPost))
            posts = result.scalars().all()

            login_user(new_user)
            return render_template('index.html', all_posts=posts, current_user=current_user)

    return render_template("register.html", form=form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email_login = request.form.get("email")
        password_login = request.form.get("password")

        user = db.session.execute(db.select(User).where(User.email == email_login)).scalar()

        if user:
            if check_password_hash(user.password, password_login):
                login_user(user)
                result = db.session.execute(db.select(BlogPost))
                posts = result.scalars().all()
                return render_template('index.html', all_posts=posts, current_user=current_user)
            else:
                flash('You email or password is incorrect')
                return redirect(url_for('login'))
        else:
            flash('You email or password is incorrect')
            return redirect(url_for('login'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:

            html_comment = form.comment.data
            soup = BeautifulSoup(html_comment, "lxml")
            text = soup.getText()

            new_comment = Comment(
                text=text,
                writer_id=current_user.id,
                post_id=post_id
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash('You must login/register first')
            return redirect(url_for('login'))
    return render_template("post.html",
                           post=requested_post,
                           current_user=current_user,
                           form=form,
                           gravatar=gravatar)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
# @admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            location=form.location.data,
            rate=form.rate.data,
            facility=', '.join(form.facility.data),
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
# @admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        location=post.location,
        rate=post.rate,
        facility=', '.join(post.facility),
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        post.rate = edit_form.rate.data
        post.facility = ', '.join(edit_form.facility.data)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
# @admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
