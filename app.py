from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from send_mail import send_mail


app = Flask(__name__)
#ENV = 'dev'
ENV = 'prod'

if ENV == 'dev':
    # local settings
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/lexus' # login@password@localhost/lexus
else:
    # deployment settings
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        customer = request.form['customer']
        dealer = request.form['dealer']
        rating = request.form['rating']
        comments = request.form['comments']
        print(customer, dealer, rating, comments)
        if '' in [customer, dealer]:
            return render_template('index.html', message="No empty field can be submitted!")
        if db.session.query(Feedback).filter(Feedback.customer == customer).count() == 0:
            # Customer does not exist
            data = Feedback(customer, dealer, rating, comments)
            db.session.add(data)
            db.session.commit()
            send_mail(customer, dealer, rating, comments)
            return render_template('success.html')
        return render_template('index.html', message="You have already submitted feedback")


if __name__ == "__main__":
    app.run()
