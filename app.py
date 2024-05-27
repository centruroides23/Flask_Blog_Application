# ----------------------------------------------- Modules Declaration ------------------------------------------------ #
from config import Config
from forms import *
import os
import smtplib
import datetime as dt
import bleach
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from flask_ckeditor import CKEditor
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import timedelta
from flask_gravatar import Gravatar
from functools import wraps


# ---------------------------------------------- Variable Declaration ------------------------------------------------ #
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
CURRENT_DATE = dt.datetime.now().date()
CURRENT_YEAR = dt.datetime.now().year

# --------------------------------------------- Application Declaration ---------------------------------------------- #
app = Flask(__name__)
app.config.from_object(Config)
ckeditor = CKEditor(app)
Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = os.environ.get("APP_SECRET_KEY")
gravatar = Gravatar(app,
                    size=150,
                    rating='p',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)


# ---------------------------------------------- Database Declaration ------------------------------------------------ #
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class BlogPost(db.Model):
    __tablename__ = "blog_post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author = relationship("Users", back_populates="posts")
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comments", back_populates="parent_post")


ACCESS = {"guest": 0, "user": 1, "admin": 2}


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    access: Mapped[int] = mapped_column(Integer)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")

    def is_admin(self):
        return self.access == ACCESS["admin"]


class Comments(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    comment_author: Mapped[str] = relationship("Users", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_post.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


# ---------------------------------------------- Function Declaration ------------------------------------------------ #
def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5',
                    'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike', 'span', 'sub', 'sup',
                    'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u', 'ul']

    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }

    cleaned = bleach.clean(content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    return cleaned


def is_user_admin():
    if not current_user.is_authenticated:
        return False
    elif not current_user.is_admin():
        return False
    else:
        return True


def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if is_user_admin():
            return function(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function

# --------------------------------------------- Application Routes --------------------------------------------------- #
@app.route("/")
def index():
    logged_in = current_user.is_authenticated
    filename = "index-bg.jpg"
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html",
                           year=str(CURRENT_YEAR),
                           date=str(CURRENT_DATE),
                           filename=filename,
                           posts=posts,
                           logged_in=logged_in,
                           is_admin=is_user_admin()
                           )


@app.route("/blog/<int:post_id>", methods=["GET", "POST"])
def get_post(post_id):
    filename = "post-bg.jpg"
    logged_in = current_user.is_authenticated
    current_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    if form.validate_on_submit():
        new_comment = Comments(comments=form.comment.data,
                               author_id=current_user.id,
                               post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("get_post", post_id=post_id))
    return render_template("post.html",
                           post=current_post,
                           filename=filename,
                           date=str(CURRENT_DATE),
                           year=str(CURRENT_YEAR),
                           logged_in=logged_in,
                           is_admin=is_user_admin(),
                           form=form)


@app.route("/add_post", methods=["GET", "POST"])
@admin_only
def add_post():
    filename = "edit-bg.jpg"
    logged_in = current_user.is_authenticated
    form = PostForm()
    if form.validate_on_submit():
        new_entry = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=CURRENT_DATE,
            body=strip_invalid_html(form.body.data),
            author_id=current_user.id,
            img_url=form.img_url.data
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("make-post.html",
                           filename=filename,
                           form=form,
                           logged_in=logged_in)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    filename = "edit-bg.jpg"
    logged_in = current_user.is_authenticated
    post = db.get_or_404(BlogPost, post_id)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        form.populate_obj(post)
        db.session.commit()
        return redirect(url_for("get_blog", post_id=post_id))
    return render_template("make-post.html",
                           filename=filename,
                           post=post,
                           form=form,
                           logged_in=logged_in)


@app.route("/delete-post/<int:post_id>")
@admin_only
def delete_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    filename = "contact-bg.jpg"
    logged_in = current_user.is_authenticated
    form = ContactForm()
    print(PASSWORD)
    if form.validate_on_submit():
        username = form.name.data
        email = form.email.data
        phone_number = form.phone.data
        message = form.message.data
        full_email = (f"Subject: Message from Philosophy Blog\n\n{message.encode('windows-1252')}\n\n\n"
                      f"From: {username}\nEmail: {email}\nPhone Number: {phone_number}")
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=USERNAME, password=PASSWORD)
            connection.sendmail(from_addr=USERNAME,
                                to_addrs=USERNAME,
                                msg=full_email)
            return redirect(url_for("receive_data"))
    return render_template("contact.html",
                           filename=filename,
                           year=str(CURRENT_YEAR),
                           logged_in=logged_in,
                           form=form)


@app.route("/about")
def about():
    filename = "about-bg.jpg"
    logged_in = current_user.is_authenticated
    return render_template("about.html",
                           filename=filename,
                           year=str(CURRENT_YEAR),
                           logged_in=logged_in)


@app.route("/form-entry")
def receive_data():
    logged_in = current_user.is_authenticated
    filename = "success-bg.jpg"
    return render_template("message_sent.html",
                           year=str(CURRENT_YEAR),
                           filename=filename,
                           logged_in=logged_in)


@app.route("/register", methods=["GET", "POST"])
def register():
    filename = "register-bg.jpg"
    form = RegisterForm()
    if form.validate_on_submit():
        current_username = form.username.data
        current_email = form.email.data
        password = generate_password_hash(password=form.password.data,
                                          method='pbkdf2:sha256',
                                          salt_length=8)

        result_username = db.session.execute(db.select(Users).where(Users.username == current_username))
        result_email = db.session.execute(db.select(Users).where(Users.email == current_email))
        username = result_username.scalar()
        email = result_email.scalar()

        if username:
            flash(message="The username already exists. Login instead!", category="danger")
            return redirect(url_for("login"))
        elif email:
            flash(message="An account with this email already exists.", category="danger")
            return redirect(url_for("register"))
        else:
            new_user = Users(username=current_username, email=current_email, password=password, access=1)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("index"))

    return render_template("register.html",
                           filename=filename,
                           form=form,
                           year=CURRENT_YEAR)


@app.route("/login", methods=["GET", "POST"])
def login():
    filename = "login-bg.jpg"
    form = LoginForm()
    logged_in = current_user.is_authenticated
    if form.validate_on_submit():
        current_username = form.username.data
        current_password = form.password.data
        result = db.session.execute(db.select(Users).where(Users.username == current_username))
        user = result.scalar()
        if not user:
            flash(message="The username does not exist", category="danger")
        elif not check_password_hash(user.password, current_password):
            flash(message="Password incorrect, please try again.", category="danger")
        else:
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html",
                           filename=filename,
                           form=form,
                           year=CURRENT_YEAR,
                           logged_in=logged_in)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False, port=5000)
