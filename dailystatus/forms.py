from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectMultipleField,SelectField,TextField,RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,Optional
from wtforms.fields.html5 import DateField
from dailystatus import app, mongo
from flask_login import login_user, current_user


class LoginForm(FlaskForm):
	email = StringField('Email',validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	submit = SubmitField('Login')


class RegisterForm(FlaskForm):
	username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
	email = StringField('Email',validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password')])
	role = SelectField('Role',validators=[DataRequired()])
	submit = SubmitField('Sign Up')

class ProjectForm(FlaskForm):
	Project = StringField('Project Name',validators=[DataRequired()])
	doc = StringField('Enter Date of Conpletion',validators=[DataRequired()])
	Cromail = StringField('CRO Email',validators=[DataRequired(), Email()])
	mailcc = StringField('Email CC',validators=[DataRequired()])
	ticketl = StringField('Ticket Link',validators=[DataRequired()])
	subject = StringField('Subject',validators=[DataRequired()])
	submit = SubmitField('submit')

def usf():
	us = []
	usr = list(mongo.db.user.find())
	for s in usr:
		us.append(s['username'])
	return us
def pjf():
	pj = []
	pjt = list(mongo.db.project_team.find())
	for i in pjt:
		pj.append(i['project_name'])
	return pj

class AssignForms(FlaskForm):
	username = SelectMultipleField('username')
	project = SelectField('project')
	submit = SubmitField('submit')

class StatusForm(FlaskForm):
	project = SelectField('Project',validators=[DataRequired()])
	date = DateField('Date',format='%Y-%m-%d',validators=[DataRequired()])
	jirano = StringField('Ticket No.',validators=[DataRequired()])
	desc = TextField('Title',validators=[DataRequired()])
	status = SelectField('username',validators=[DataRequired()])
	env = SelectField('Env',validators=[DataRequired()])
	comments = TextField('Comment', validators=[DataRequired()])
	submit = SubmitField('submit')

class View_statusForm(FlaskForm):
	project = SelectField('Project',validators=[DataRequired()])
	username = SelectField('Username')
	date = DateField('Date',format='%Y-%m-%d',validators=[DataRequired()])
	mailcc = StringField('cc : ')
	mailbcc = StringField('bcc : ')
	to = StringField('To : ')
	subject = StringField('Subject : ')	
	submit = SubmitField('submit')
	#SendMail = RadioField('Send Mail',choices=[('value','Send Mail')])


class DeleteForms(FlaskForm):
	username = SelectField('username',validators=[Optional()])
	project = SelectField('project',validators=[Optional()])
	radio = RadioField('Select Option', choices=[('user', 'Delete User'), ('project', 'Delete Project'), ('userdel', 'Delete a user from a project '), ('disable', 'Deactivate/Activate a user')])
	submit = SubmitField('submit')

class ChangeForm(FlaskForm):
	current_password = PasswordField('Current Password', validators=[DataRequired()])
	new_password = PasswordField('New Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('new_password')])
	role = SelectField('Role',validators=[DataRequired()])
	submit = SubmitField('Submit')



