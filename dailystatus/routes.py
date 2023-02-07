from flask import render_template, url_for, flash, redirect, request,session,jsonify
from dailystatus import app, mongo, bcrypt,login_manager,mail,cache
from bson.json_util import dumps
from dailystatus.forms import LoginForm,RegisterForm,ProjectForm,AssignForms,StatusForm,DeleteForms,View_statusForm,ChangeForm
from flask_login import login_user, current_user, logout_user, login_required,UserMixin
from bson.objectid import ObjectId
import json
from flask_mail import Message
from datetime import datetime


class JSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, ObjectId):
			return str(o)
		return json.JSONEncoder.default(self, o)

class User(UserMixin):
	def __init__(self, email):
		self.email = email
	def get_id(self):
		return self.email

def verify():
	em = current_user.get_id()
	User = mongo.db.user
	user = User.find_one({"mail_id":em})
	if user['role'] == "admin":
		return True
	else:
		return False

def suffix(d):
	return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
	return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

@login_manager.user_loader
def load_user(email):
	u = mongo.db.user.find_one({"mail_id" : email })
	if not u:
		return None
	return User(email=u['mail_id'])

@app.route("/")
@app.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()
	Uer = mongo.db.user
	if form.validate_on_submit():
		user = Uer.find_one({"mail_id": form.email.data,"Active":True})
		if user is not None and bcrypt.check_password_hash(user['password'], form.password.data):
			user_obj = User(email=user['mail_id'])
			login_user(user_obj)
			next_page = request.args.get('next')
			if user['role'] == "admin":
				return (redirect(url_for('Register')) if next_page else redirect(url_for('Register')))
			else:
				return (redirect(url_for('StatusUpdate')) if next_page else redirect(url_for('StatusUpdate')))
		else:
			flash('Login Unsuccessful. Please check email and password', 'danger')
	return render_template('login.html', title='Login', form=form)


@app.route("/register", methods=['GET', 'POST'])
@login_required
@cache.memoize(50)
def Register():

	if current_user.is_authenticated:
		if verify():
			pass
		else:
			return redirect(url_for('StatusUpdate'))
	else:
		return redirect(url_for('login'))
	User = mongo.db.user
	form = RegisterForm()
	# if form.username.data and form.email.data and form.password.data and form.confirm_password.data and form.role.data is not None:
	if all(v is not None for v in [form.username.data,form.email.data,form.password.data,form.confirm_password.data]) and form.role.data != '':	
	# if form.validate_on_submit():
		if form.password.data == form.confirm_password.data:
			hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
			user = User.find_one({"mail_id": form.email.data})
			usern = User.find_one({"username": form.username.data})
			if all(v is None for v in [user,usern]):
				try:
					cre = form.password.data
					msg = Message('Your account has been created on Daily Status',sender= 'shwetangdemo@gmail.com',recipients = [form.email.data])
					msg.html = render_template('Cred.html', cre=cre)
					#mail.send(msg)
					User.insert({"username" : form.username.data, "mail_id" : form.email.data, "password" : hashed_password,"role" : form.role.data,"Active":True})
					flash('Your account has been created! You are now able to log in', 'success')
					return render_template('register.html', title='Register', form=form)
				except:
					flash('Enter Valid Email ID','danger')
				return render_template('register.html', title='Register', form=form)
			else:
				flash('Email id or username already exist! Enter new Username or Email', 'danger')
		else:
			flash('password and confirm password must be same','danger')


	return render_template('register.html', title='Register', form=form)

@app.route("/Assign",methods=['GET','POST'])
@login_required
@cache.memoize(50)
def Assign():
	if current_user.is_authenticated:
		if verify():
			pass
		else:
			return redirect(url_for('StatusUpdate'))
	else:
		return redirect(url_for('login'))
	form = AssignForms()
	choices = list(mongo.db.user.find({"Active":True}))
	choicesp = list(mongo.db.project_team.find())
	User = mongo.db.user
	Project = mongo.db.project_team
	if form.username.data and form.project.data is not None:
		for us in form.username.data: 
			NAU = Project.find_one({"project_name":form.project.data,"team_member.username":us})
			if NAU is None:
				teammember = User.find_one({"username" : us}, {"_id":0, "projects":0})
				Project.update({"project_name":form.project.data},{"$push":{"team_member":teammember}})
				User.update({"username":us},{ "$push":{"projects":form.project.data}})
				flash('Team-member '+us+' has been added!','success')
			else:
				flash('Team-member '+us+' is already part of team!','danger')

		return redirect(url_for('Assign'))

	return render_template('Assign.html',title='assign',form=form,choices=choices,choicesp=choicesp)

@app.route("/registerproject", methods=['GET', 'POST'])
@login_required
def RegisterProject():
	if current_user.is_authenticated:
		if verify():
			pass
		else:
			return redirect(url_for('StatusUpdate'))
	else:
		return redirect(url_for('login'))
	form = ProjectForm()
	Project = mongo.db.project_team
	if form.validate_on_submit():

		pro = Project.find_one({"project_name": form.Project.data})
		if pro is None:
			Project.insert({"project_name" :form.Project.data,"doc":form.doc.data,"Cromail" :form.Cromail.data,"mailcc":form.mailcc.data,'subject':form.subject.data,"ticketl":form.ticketl.data})
			flash('Your project has been created!', 'success')
			return redirect(url_for('RegisterProject'))
		else:
			flash('Projectname already exist! Enter new Projectname', 'danger')
	return render_template('registerproject.html', title='RegisterProject', form=form)

@app.route("/statusupdate", methods=['GET', 'POST'])
@login_required
def StatusUpdate():
	if current_user.is_authenticated:
		if verify():
			return redirect(url_for('Register'))
		else:
			pass
	else:
		return redirect(url_for('login'))
	TaskS = mongo.db.task_status
	TaskUD = mongo.db.task_status_ud
	em = current_user.get_id()
	form = StatusForm()
	def usd():
		usr = []
		usf = list(mongo.db.user.find({'mail_id':em}))
		for i in usf:
			s = i['projects']
			for e in s:
				usr.append(e)
		return usr
	choices = usd()
	usr = mongo.db.user.find_one({"mail_id":em})
	if form.project.data and form.date.data and form.jirano.data and form.status.data and form.env.data is not None:
		date= form.date.data.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
		iso_date = datetime.strptime(date,"%Y-%m-%dT%H:%M:%S.%fZ")
		comments = []
		if isinstance(form.comments.data,str):
			comment=form.comments.data.strip()
		if "\n" in comment:
			comments = comment.split("\n")
		else:
			comments.append(comment)
		if isinstance(form.jirano.data,str):
			form.jirano.data = form.jirano.data.strip()
		if form.env.data == 'Development Status':
			sd = TaskS.find_one({"project_name":form.project.data,"username":usr['username'],"date":iso_date,"env":form.env.data})
			if sd is None:
				TaskS.insert({"project_name":form.project.data ,'mail_id':em, "username":usr['username'] , "date":iso_date,"env": form.env.data ,"status":[{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}]})
				flash('Your status has been updated','success')
			else:
				TaskS.update({"project_name":form.project.data,"date":iso_date,"username":usr['username']},{"$push":{"status":{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}}})
				flash('Your status has been updated','success')
		else:
			sd = TaskUD.find_one({"project_name":form.project.data,"username":usr['username'],"date":iso_date})
			if sd is None:
				TaskUD.insert({"project_name":form.project.data ,'mail_id':em, "username":usr['username'] , "date":iso_date,"pstatus":[{"env":form.env.data ,"status":[{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}]}]})
				flash('Your status has been updated','success')
			else:
				vk = TaskUD.find_one({"project_name":form.project.data,"username":usr['username'],"date":iso_date,"pstatus.env":form.env.data})
				if vk is not None:
					TaskUD.update({"project_name":form.project.data,"date":iso_date,"username":usr['username'],"pstatus.env":form.env.data},{"$push":{"pstatus.$.status":{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}}})
					flash('Your status has been updated','success')
				else:
					TaskUD.update({"project_name":form.project.data,"date":iso_date,"username":usr['username']},{"$push":{"pstatus":{"env":form.env.data ,"status":[{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}]}}})
					# TaskUD.update({"project_name":form.project.data , "username":usr['username'] , "date":iso_date},{"$push":{"pstatus.$.env":form.env.data}})
					# TaskUD.update({"project_name":form.project.data,"date":iso_date,"username":usr['username'],"pstatus.$.env":form.env.data},{"$push":{"pstatus.$.status":{"jira_no":form.jirano.data , "desc":form.desc.data , "status":form.status.data, "Comment":comments}}})
					flash('Your status has been updated','success')			
		return redirect(url_for('StatusUpdate'))
	return render_template('statusupdate.html', title='StatusUpdate', form=form,choices=choices)

@app.route("/delete", methods=['GET', 'POST'])
@login_required
def DeleteD():
	if current_user.is_authenticated:
		if verify():
			pass
		else:
			return redirect(url_for('StatusUpdate'))
	else:
		return redirect(url_for('login'))
	User = mongo.db.user
	project = mongo.db.project_team
	form = DeleteForms()
	choices = list(mongo.db.user.find())
	choicesp = list(mongo.db.project_team.find())
	if form.radio.data == "user":
		if form.username.data is not None:
			project.update({},{"$pull":{"team_member":{"username":form.username.data}}}, multi=True)
			User.remove({"username":form.username.data})
			#msg = mongo.db.runCommand({"getLastError": 1})
			flash('user removed successfully '+form.username.data,'success')
			return redirect(url_for('DeleteD'))
	elif form.radio.data == "project":
		if form.project.data is not None:
			User.update({},{'$pull':{'projects':form.project.data}}, multi=True)
			project.remove({'project_name':form.project.data})
			flash('Project removed successfully '+form.project.data,'success')
			return redirect(url_for('DeleteD'))
	elif form.radio.data == "userdel":
		if form.project.data and form.username.data is not None:
			project.update_one({'project_name':form.project.data},{'$pull':{'team_member':{'username':form.username.data}}})
			User.update_one({'username':form.username.data},{'$pull':{'projects':form.project.data}})
			flash('user removed successfully '+form.radio.data,'success')
			return redirect(url_for('DeleteD'))
	elif form.radio.data == "disable":
		if form.username.data is not None:
			use = User.find_one({"username":form.username.data},{"Active":1})
			if use['Active'] == True:
				User.update({"username":form.username.data},{"$set":{"Active":False}})
				flash('user deactivated successfully','success')
			else:
				User.update({"username":form.username.data},{"$set":{"Active":True}})
				flash('user activated successfully','success')
			return redirect(url_for('DeleteD'))
	return render_template('delete.html', title='Delete', form=form,choicesp=choicesp,choices=choices)


@app.route("/username/<project>",methods=['GET','POST'])
def username(project):
	user = list(mongo.db.project_team.find({'project_team':project},{'team_member':1}))
	users = []
	for s in user['team_member']:
		users.append(s['username'])
	return jsonify ({"users" : users})

@app.route("/viewstatus", methods=['GET', 'POST'])
@login_required
def View_status():
	form = View_statusForm()
	if current_user.is_authenticated:
		if verify():
			return redirect(url_for('Register'))
		else:
			pass
	else:
		return redirect(url_for('login'))
	stat = []
	em = current_user.get_id()
	def usd():
		usr = []
		usf = list(mongo.db.user.find({'mail_id':em}))
		for i in usf:
			s = i['projects']
			for e in s:
				usr.append(e)
		return usr
	choicesp = usd()
	Status = mongo.db.task_status
	Status_ud = mongo.db.task_status_ud
	project = mongo.db.project_team
	if form.project.data and form.date.data is not None:
		date= form.date.data.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
		iso_date = datetime.strptime(date,"%Y-%m-%dT%H:%M:%S.%fZ")
		stat = list(Status.find({"project_name" : form.project.data, "date" :iso_date, "env":'Development Status'}))
		remstat = list(Status_ud.find({"project_name" : form.project.data, "date" :iso_date}))
		cc = project.find_one({"project_name":form.project.data},{"mailcc":1,"Cromail":1,"ticketl":1,"subject":1,"_id":0})
		em=[]
		abc = Status.find({"project_name":form.project.data,"date":iso_date},{"mail_id":1,"_id":0})
		efg = Status_ud.find({"project_name":form.project.data,"date":iso_date},{"mail_id":1,"_id":0})
		for i in abc:
			if i['mail_id'] not in em:
				em.append(i['mail_id'])
		for i in efg:
			if i['mail_id'] not in em:
				em.append(i['mail_id'])
		bcc = ";".join(em)
		formatdate = custom_strftime('{S} %B %Y', form.date.data)
		sub = cc['subject'] + ' Status Update of ' + formatdate

		return render_template('view-status.html', form=form, stat=stat, cc=cc,sub=sub, bcc=bcc, remstat=remstat, choicesp=choicesp, formatdate=formatdate)
	return render_template('view-status.html', form=form,choicesp=choicesp)

@app.route("/changepassword", methods=['GET', 'POST'])
@login_required
def changepassword():
	User = mongo.db.user
	if current_user.is_authenticated:
		if verify():
			return redirect(url_for('StatusUpdate'))
		else:
			pass
	else:
		return redirect(url_for('login'))
	form = ChangeForm()
	em = current_user.get_id()
	current_pass = User.find_one({"mail_id": em})
	if form.new_password.data and form.current_password.data is not None:
		if current_pass is not None and bcrypt.check_password_hash(current_pass['password'], form.current_password.data):
			hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
			User.update({"mail_id" : em},{"$set": {"password" : hashed_password}})
			flash('your password has been changed', 'success')
			return redirect(url_for('changepassword'))
		else:
			flash('Wrong password, Please check', 'danger')
	return render_template('changepassword.html', title='ChangePassword', form=form)

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))



