from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import or_
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///postdata.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(20), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    post_date = db.Column(db.DateTime, nullable=False)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(20), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    post_date = db.Column(db.DateTime, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    question = db.relationship('Question', backref=db.backref('answers', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/')
def index():
    questions = Question.query.all()
    return render_template('index.html', questions=questions)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = generate_password_hash(request.form.get('password'))
            user = User.query.filter_by(username=username).first()

            if user == None:
                user = User(username=username, password=password)
                db.session.add(user)
                db.session.commit()
                return render_template('login.html')
            else:
                return render_template('login.html')
        else:
            return render_template('signup.html')

    except ValueError as e:
        return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user == None:
            return render_template("signup.html")

        elif check_password_hash(user.password, password):
            login_user(user)
            return render_template('index.html')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/question', methods=['GET', 'POST'])
def question():
    if request.method == 'POST':
        user = request.form['user']
        detail = request.form['detail']
        post_date = datetime.now()
        question = Question(user=user, detail=detail, post_date=post_date)
        db.session.add(question)
        db.session.commit()
        return redirect('/')
    else:
        questions = Question.query.all()
        return render_template('question.html', questions=questions)

@app.route('/detail/<int:question_id>')
def detail(question_id):
    question = Question.query.get(question_id)
    answers = Answer.query.filter(Answer.question_id == question_id).all()
    return render_template('detail.html', question=question, answers=answers)

@app.route('/answer/<int:question_id>', methods=['GET', 'POST'])
def answer(question_id):
    if request.method == 'POST':
        user = request.form['user']
        detail = request.form['detail']
        post_date = datetime.now()
        answer = Answer(user=user, detail=detail, post_date=post_date, question_id=question_id)
        db.session.add(answer)
        db.session.commit()
        return redirect('/')
    else:
        question = Question.query.get(question_id)
        return render_template('answer.html', question=question)

@app.route('/search_word', methods=['POST'])
def searching():
    text_input = request.form['search']
    if text_input is None or len(text_input) == 0:
        questions = Question.query.all()
        return render_template('index.html', questions=questions)
    else:
        questions = db.session.query(Question).filter(or_(Question.detail.contains(text_input))).all()
        return render_template('index.html', questions=questions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
