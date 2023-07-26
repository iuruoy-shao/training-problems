from flask import Flask, render_template, redirect, request, Blueprint, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'amc10_problems.db')
app.config['SECRET_KEY'] = "test"
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test = db.Column(db.String, nullable=False)
    number = db.Column(db.Integer)
    choices = db.Column(db.String)
    problem_content = db.Column(db.String(), nullable=False)
    answer = db.Column(db.String, nullable=False)
    solutions = db.Column(db.String)
    labels = db.Column(db.String)
    difficulty = db.Column(db.Integer)

    def __repr__(self):
        return f'{self.AMC_name()} Problem {self.number}'
    
    def AMC_name(self):
        return f'{self._test()[0]} AMC {self._test()[1]}{self._test()[2]}'
    def _test(self):
        return json.loads(self.test)
    def _choices(self):
        return json.loads(self.choices)
    def get_choice(self,letter):
        return self._choices[['A','B','C','D','E'].index(letter)]
    def _labels(self):
        return json.loads(self.labels)

class ProblemHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    completion = db.Column(db.Integer, nullable=False, default=0)
    last_attempted = db.Column(db.String)
    previous_answers = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'id: {self.problem_id} \nattempts: {self.attempts}'

    def _previous_answers(self):
        try:
            return json.loads(self.previous_answers)
        except Exception:
            return []
    def append_answer(self,x):
        answers = self._previous_answers()
        answers.append(f"{x}")
        self.previous_answers = json.dumps(answers)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    problems_history = db.relationship('ProblemHistory', backref='user', lazy='dynamic')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        if not db.session.execute(db.select(User).where(User.username == username)).first():
            user = User(username=request.form.get('username'),
                        password=request.form.get('password'))
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            render_template('register.html',username_unique=False)
    return render_template('register.html',username_unique=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form.get('username')).first()
        if user and user.password == request.form.get('password'):
                login_user(user)
                return redirect(url_for('index'))
        else:
            return render_template('login.html',user_not_found=True)
    return render_template('login.html',user_not_found=False)

@app.route('/')
def index():
    return redirect('/problems/1')

@app.route('/problems/<int:problem_id>', methods=['GET','POST'])
def render(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    if not current_user.problems_history.filter_by(problem_id=problem_id).first():
        db.session.add(ProblemHistory(problem_id=problem_id, user_id=current_user.id))
        db.session.commit()
    problem_history = current_user.problems_history.filter_by(problem_id=problem_id).first()

    if request.method == 'POST' and problem_history.completion == 0:
        problem_history.last_attempted = datetime.now()
        problem_history.attempts += 1

        answer = request.form['choices']
        problem_history.append_answer(answer)
        if answer == problem.answer:
            problem_history.completion = 1
        db.session.commit()
    if request.method == 'POST' and problem_history.completion == 1:
        redirect(url_for('next_problem'))
    return render_template('display_problems.html',
                    choices=['A','B','C','D','E'],
                    problem=problem,
                    problem_history=problem_history)

@app.route('/next_problem')
def next_problem():
    redirect('/')

if __name__ == '__main__':
    app.run(port=8000,debug=True)