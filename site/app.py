from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime
from operator import attrgetter
import werkzeug
import random
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'amc10_problems.db')
app.config['SECRET_KEY'] = "test"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Converts labels from [0,0,0,0,0] format to list of labels (ex: ['Algebra','Geometry'])
label_to_categories = lambda labels: [AllStatistics.query.first().category_names()[i] for i, label in enumerate(labels) if label]

# Stores the category/label names and the number of problems in that category in a dictionary.
class AllStatistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_counts = db.Column(db.String, nullable=False, 
                                default=json.dumps({"Miscellaneous": 0, "Algebra": 0, "Geometry": 0, "Number Theory": 0, "Combinatorics": 0}))

    def _category_counts(self):
        return json.loads(self.category_counts.replace("\'", "\""))
    def num_categories(self):
        return len(self._category_counts())
    def category_names(self):
        return list(self._category_counts().keys())
    def update_counts(self):
        counts = {"Miscellaneous": 0, "Algebra": 0, "Geometry": 0, "Number Theory": 0, "Combinatorics": 0}
        for problem in Problem.query.all():
            counts = {category: counts[category] + problem._labels()[i] for i, category in enumerate(self._category_counts().keys())}
        self.category_counts = str(counts)
    def count_of(self,category):
        return self._category_counts()[category]

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
    def label_names(self):
        return label_to_categories(self._labels())
    def in_category(self,category):
        return category in self.label_names()
    
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
        if x not in answers:
            answers.append(f"{x}")
            self.last_attempted = datetime.now()
            self.attempts += 1
        self.previous_answers = json.dumps(answers)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    problems_history = db.relationship('ProblemHistory', backref='user', lazy='dynamic')
    performance = db.Column(db.String(2000), nullable=False)
    
    def _performance(self,category=None):
        parsed_performance = json.loads(self.performance.replace("\'", "\""))
        return parsed_performance[category] if category else parsed_performance
    def mastery(self, category):
        MASTERY = 5
        n = 0
        for problem_history in self.problems_history.filter(ProblemHistory.attempts > 0).all():
            problem = Problem.query.get_or_404(problem_history.problem_id)
            n+=1 if (category in label_to_categories(problem._labels())) and (problem.difficulty > 3) else 0
        return n >= MASTERY
    
    # status is 0 when category is untouched, 1 if decreasing in performance, 2 if increasing in performance, and 3 if mastered
    def update_cat_score(self,category,score):
        performance = self._performance()
        c = performance[category]['completed']
        s0 = performance[category]['score']
        s = (score + performance[category]['score']*c)/(c+1)
        performance[category]['score'] = s
        if performance[category]['status'] < 3:
            if self.mastery(category):
                performance[category]['status'] = 3
            elif s < s0:
                performance[category]['status'] = 1
            elif s > s0:
                performance[category]['status'] = 2
        self.performance = json.dumps(performance)
    def update_cat_completion(self,category,n=1):
        performance = self._performance()
        performance[category]['completed'] += n
        self.performance = json.dumps(performance)
    def get_last_attempted(self,n=3,*categories):
        """
        Gathers at most n last attempted problem ids in categories
        """
        if not categories:
            return [
                Problem.query.get_or_404(item.problem_id)
                for item in self.problems_history
                .order_by(ProblemHistory.last_attempted.desc())
                .limit(n)
            ]
        in_category = [
            problem_history
            for problem_history in self.problems_history.all()
            if (set(Problem.query.get_or_404(problem_history.problem_id).label_names()) & {categories})
        ]
        # return [in_category.order_by(ProblemHistory.last_attempted.desc()).limit(n)]
        # return max(in_category,key=attrgetter('last_attempted'))
        return sorted(enumerate(in_category), key=attrgetter('last_attempted'))[:n]

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
                        password=request.form.get('password'),
                        performance = str({category : {"score":50.0,"status":0,"completed":0} 
                                           for category in AllStatistics.query.first().category_names()}))
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
@login_required
def index():
    try:
        problem_id = current_user.get_last_attempted(n=1)[0].id
    except Exception:
        problem_id = 1
    return redirect(f'/problems/{problem_id}')

@app.route('/problems/<int:problem_id>', methods=['GET','POST'])
@login_required
def render(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    if not current_user.problems_history.filter_by(problem_id=problem_id).first():
        db.session.add(ProblemHistory(problem_id=problem_id, user_id=current_user.id))
        db.session.commit()
    problem_history = current_user.problems_history.filter_by(problem_id=problem_id).first()

    if request.method == 'POST' and problem_history.completion == 0:
        try:
            answer = request.form['choices']
            problem_history.append_answer(answer)
            if answer == problem.answer:
                problem_history.completion = 1
            db.session.commit()
        except werkzeug.exceptions.BadRequestKeyError:
            pass
    if request.method == 'POST' and request.form.get("Next Problem"):
        return redirect(url_for('next_problem', ph_id = problem_history.id))
    return render_template('display_problems.html',
                    choices=['A','B','C','D','E'],
                    problem=problem,
                    problem_history=problem_history)

@app.route('/next_problem/<int:ph_id>')
@login_required
def next_problem(ph_id):
    problem_history = current_user.problems_history.filter_by(id=ph_id).first()
    problem = Problem.query.get_or_404(problem_history.problem_id)
    labels = problem._labels()
    problem_score = (5-problem_history.attempts)*25 * (1 + (problem.difficulty - 1)*.25)
    
    for label in label_to_categories(labels):
        current_user.update_cat_score(label,problem_score)
        current_user.update_cat_completion(label)
        db.session.commit()
    
    return redirect(url_for('recommend_problem'))

@app.route('/recommend')
@login_required
def recommend_problem():
    # picks category based on weighted probability and non-mastery
    categories = []
    weights = []
    for category in current_user._performance():
        if current_user._performance()[category]['status'] < 3:
            categories.append(category)
            weights.append(current_user._performance()[category]['score'])
    category = random.choices(categories,weights)[0]
    print(category)
    
    # Picks a problem with difficulty matching the status
    last_attempted = current_user.get_last_attempted(1,category)
    print(last_attempted)
    if last_attempted:
        last_completed_difficulty = Problem.query.get_or_404(last_attempted[0].problem_id).difficulty
        match current_user._performance()[category]['status']:
            case 1:
                difficulty = last_completed_difficulty - 1 if last_completed_difficulty > 1 else 1
            case 2:
                difficulty = last_completed_difficulty + 1 if last_completed_difficulty < 5 else 5
    else:
        difficulty = 3
    next_problem_id = query_problems(category, difficulty=difficulty)
    print(next_problem_id)
    return redirect(url_for('render', problem_id = next_problem_id))


def query_problems(category, difficulty=3, approx_difficulty=True, allow_completed=True):
    """
    Returns the id of a problem with the given category
    approx_difficulty: if none with the given difficulty could be found, one of the closest difficulty will be used
    allow_completed: if none incompleted could be found, one that is completed will be picked
    """
    # filter_difficulties = lambda x : Problem.query.filter(Problem.in_category(category),
    #                                                       Problem.difficulty in x,
    #                                                       current_user.problems_history.filter_by(problem_id=Problem.id).first().attempts > 0).all()
    filter_difficulties = lambda x : [problem for problem in Problem.query.all() 
                                      if problem.in_category(category) 
                                      and problem.difficulty in x 
                                      and (not current_user.problems_history.filter_by(problem_id=problem.id).first() 
                                           or not current_user.problems_history.filter_by(problem_id=problem.id).first().completion)]
    difficulties = [difficulty]
    filtered = filter_difficulties(difficulties)

    while not filtered and {1, 2, 3, 4, 5}.issubset(difficulties):
        difficulties.append(max(difficulties)+1)
        difficulties.append(min(difficulties)-1)
        filtered = filter_difficulties(difficulties)
    
    if not filtered:
        return random.choice(Problem.query.filter(Problem.in_category(Problem, category)).all()).id
    else:
        return random.choice(filtered).id

if __name__ == '__main__':
    app.run(port=8000,debug=True)