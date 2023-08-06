from flask import Flask, render_template, request, redirect, url_for, flash
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

# テーブル作成
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

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=False, index=True)
    description = db.Column(db.String(200), nullable=False)

# ログインが必要なページにアクセスした際にログインページにリダイレクトする
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

# ログインなどの処理を行う
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
                return render_template('login.html', text='登録完了しました。')
            else:
                return render_template('login.html', text='ユーザー名が既に使用されているか、パスワードが異なります。')
        else:
            return render_template('signup.html', text='error')

    except ValueError as e:
        print(e)
        return render_template('login.html', text='ユーザー名が既に使用されているか、パスワードが異なります')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()

            if user == None:
                return render_template('login.html', text='ユーザー名が既に使用されているか、パスワードが異なります')

            elif check_password_hash(user.password, password):
                login_user(user)
                return render_template('index.html', text='ログイン完了しました')

            else:
                return render_template('login.html', text='ユーザー名が既に使用されているか、パスワードが異なります')

        else:
            return render_template('login.html')

    except ValueError as e:
        print(e)
        return render_template('login.html', text = 'error')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

# 質問などの処理を行う
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

# 学生ステーション問い合わせフォーム
@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/contact/complete", methods=["GET", "POST"])
def contact_complete():
    if request.method == "POST":
        # フォームの値を取得する
        if not request.form["username"] or not request.form["email"] or not request.form["description"]:
            flash("入力してください")
            return redirect(url_for("contact"))
        else:
            username = request.form["username"]
            email = request.form["email"]
            description = request.form["description"]

            post = Post(username=username, email=email, description=description)
            db.session.add(post)
            db.session.commit()
            flash("問い合わせ内容はメールに送信しました。問い合わせありがとうございました。")
            return redirect(url_for("contact_complete"))

    else:
        return render_template("contact_complete.html")

if __name__ == '__main__':
    app.run(debug=True)
