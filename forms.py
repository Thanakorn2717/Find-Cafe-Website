from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from wtforms.widgets import ListWidget, CheckboxInput


RATE = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]
FACILITY = [('POWER', 'POWER'), ('WIFI', 'WIFI')]
# WTForm for creating a blog post


class CreatePostForm(FlaskForm):
    title = StringField("Cafe's name", validators=[DataRequired()])
    subtitle = StringField("Description", validators=[DataRequired()])
    img_url = StringField("img_url", validators=[DataRequired(), URL()])
    location = StringField("Location", validators=[DataRequired(), URL()])
    rate = SelectField("Rate", choices=RATE, validators=[DataRequired()])
    facility = SelectMultipleField("Facilities", choices=FACILITY, option_widget=CheckboxInput(),
                                   widget=ListWidget(prefix_label=False), validators=[DataRequired()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LET ME IN!")


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField(label='Comment', validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
