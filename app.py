from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_sqlalchemy import SQLAlchemy
from send_mail import send_mail

import os
import datetime
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, BooleanField
from passlib.hash import sha256_crypt

app = Flask(__name__)
#ENV = 'dev'
ENV = 'prod'

if ENV == 'dev':
    # local settings
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/lexus' # login@password@localhost/lexus
else:
    # deployment settings
    app.secret_key = "secret_123"
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://jedzmkraftckgq:241e6d422e21825ad723b131348c30b2dcccee2df1283519cc027ea06868b1ae@ec2-174-129-33-186.compute-1.amazonaws.com:5432/dan4uc1ma8ed1b'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# create db object
db = SQLAlchemy(app)

# Create Model
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(200), unique=True)
    dealer = db.Column(db.String(200))
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text())

    def __init__(self, customer, dealer, rating, comments):
        self.customer = customer
        self.dealer = dealer
        self.rating = rating
        self.comments = comments

# Create Model
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    email = db.Column(db.String(200), unique=True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))
    register_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = password

def get_user(username):
    ret = db.session.query(Users).filter(Users.username == username).first()
    print(ret)
    if ret is None:
        return None
    return ret.__dict__

def create_user(name, email, username, password):
    data = Users(name, email, username, password)
    db.session.add(data)
    db.session.commit()

def get_all_feedbacks():
    rows = db.session.query(Feedback).all()
    print(rows)
    return rows

def get_dealer_feedbacks(dealer):
    rows = db.session.query(Feedback).filter(Feedback.dealer == dealer).all()
    print(rows)
    return rows

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please log in', 'danger')
			return redirect(url_for('login'))
	return wrap

class RegistrationForm(Form):
	name = StringField('Name', [validators.Length(min=4, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=50)])
	email = StringField('Email Address', [validators.Length(min=6, max=150)])
	password = PasswordField('New Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords must match')
		])
	confirm = PasswordField('Repeat Password')

# Registration form
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		create_user(name, email, username, password)
		flash("You are now registered and login", "success")
		return redirect(url_for('index'))
	return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form fields
		username = request.form['username']
		password_candidate = request.form['password']
		data = get_user(username)
		print(data)
		if data is not None:
			# Get stored hash
			password = data['password']
			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):
				 app.logger.info('Password Matched!!!')
				 session['logged_in'] = True
				 session['username'] = username
				 flash('You are now logged in', 'success')
				 return redirect(url_for('feedback'))
			else:
				app.logger.info('...... ..... Password did not match!!!')
				error = "Invalid Password"
				return render_template('login.html', error=error)
		else:
			app.logger.info('NO user found')
			error = "Username not found"
			return render_template('login.html', error=error)
	return render_template('login.html')

# User logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash("You are logged out", 'success')
	return redirect(url_for('login'))

@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("home.html")

@app.route("/about")
def about():
	return render_template("about.html")

@app.route('/feedback')
@is_logged_in
def feedback():
    return render_template('feedback.html')

@app.route('/submit', methods=['POST'])
@is_logged_in
def submit():
    if request.method == 'POST':
        customer = request.form['customer']
        dealer = request.form['dealer']
        rating = request.form['rating']
        comments = request.form['comments']
        print(customer, dealer, rating, comments)
        if '' in [customer, dealer]:
            return render_template('feedback.html', message="No empty field can be submitted!")
        if db.session.query(Feedback).filter(Feedback.customer == customer).count() == 0:
            # Customer does not exist
            data = Feedback(customer, dealer, rating, comments)
            db.session.add(data)
            db.session.commit()
            send_mail(customer, dealer, rating, comments)
            return render_template('success.html')
        return render_template('feedback.html', message="You have already submitted feedback")

@app.route("/all_feedbacks")
@is_logged_in
def all_feedbacks():
	feedbacks = get_all_feedbacks()
	app.logger.info(feedbacks)
	if feedbacks:
		return render_template('all_feedbacks.html', feedbacks=feedbacks)
	else:
		msg = '''No feedback found'''
		return render_template('all_feedbacks.html', msg=msg)

@app.route("/all_feedbacks/<string:dealer>/")
@is_logged_in
def dealer_feedbacks(dealer):
    feedbacks = get_dealer_feedbacks(dealer)
    return render_template("show_feedback.html", feedbacks=feedbacks)


if __name__ == "__main__":
    app.secret_key = "secret_123"
    app.run()
