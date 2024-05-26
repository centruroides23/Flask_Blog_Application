from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import URL, InputRequired, Email, Regexp, Length
from flask_ckeditor import CKEditorField


class PostForm(FlaskForm):
    title = StringField(label="Title:", validators=[InputRequired()])
    subtitle = StringField(label="Subtitle", validators=[InputRequired()])
    # author = StringField(label="Author", validators=[InputRequired()])
    img_url = StringField(label="Image URL", validators=[InputRequired(), URL()])
    body = CKEditorField(label="Title Body", validators=[InputRequired()])
    submit = SubmitField(label="Post!")


class CommentForm(FlaskForm):
    comment = CKEditorField(label="Submit Comment")
    submit = SubmitField(label="Comment")


class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[InputRequired()])
    email = StringField(label="Email Address", validators=[InputRequired(), Email()])
    phone = StringField(label="Phone Number", validators=[InputRequired()])
    message = StringField(label="Message", validators=[InputRequired()])
    submit = SubmitField(label="Send Message")


class RegisterForm(FlaskForm):
    username = StringField(label='Username',
                           validators=[InputRequired(),
                                       Regexp('^[a-zA-Z0-9_-]+$',
                                              message="Username must contain only letters, numbers, underscores,"
                                                      " or hyphens.")])
    email = StringField(label="Email", validators=[InputRequired(), Email()])
    password = PasswordField(label="Password",
                             validators=[InputRequired(),
                                         Length(min=8,
                                                max=20,
                                                message="Password must contain 8 to 20 characters"),
                                         Regexp(
                                             regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$",
                                             message=("Password must contain at least one uppercase letter, one "
                                                      "lowercase letter, one digit, and one special character."))
                                         ]
                             )
    submit = SubmitField(label="Register")


class LoginForm(FlaskForm):
    username = StringField(label='Username',
                           validators=[InputRequired()])
    password = PasswordField(label="Password",
                             validators=[InputRequired()])
    submit = SubmitField(label="Register")