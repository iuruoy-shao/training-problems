import contextlib
from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from datetime import datetime
from operator import attrgetter
import validate_email
import werkzeug
import random
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'amc10_problems.db')
app.config['SECRET_KEY'] = "test"
convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db, render_as_batch=True)

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
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))

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
        current_user._current_profile().last_active = datetime.now()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    profiles = db.relationship('Profile', backref='user', lazy='dynamic')
    current_profile = db.Column(db.Integer, nullable=False, default=1)
    
    def _current_profile(self):
        '''
        Returns the Profile object with id corresponding to the value of current_profile
        '''
        return Profile.query.get_or_404(self.current_profile)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    problems_history = db.relationship('ProblemHistory', backref='profile', lazy='dynamic')
    performance = db.Column(db.String(2000), nullable=False)
    preferred_categories = db.Column(db.String(2000), nullable=False, default='[]') # whitelisted categories (list)
    date_created = db.Column(db.String)
    last_active = db.Column(db.String)

    def __repr__(self):
        return f"""{self.name}: {self.total_completed()} problems completed, 
        created on {datetime.strptime(self.date_created, "%Y-%m-%d %H:%M:%S.%f").date()}, 
        last active on {datetime.strptime(self.last_active, "%Y-%m-%d %H:%M:%S.%f").date()}"""

    def _date_created(self):
        return datetime.strptime(self.date_created, "%Y-%m-%d %H:%M:%S.%f").date()
    def _last_active(self):
        return datetime.strptime(self.last_active, "%Y-%m-%d %H:%M:%S.%f").date()
    def _performance(self,category=None):
        parsed_performance = json.loads(self.performance.replace("\'", "\""))
        return parsed_performance[category] if category else parsed_performance
    def _preferred_categories(self):
        return json.loads(self.preferred_categories.replace("\'", "\""))
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
        c = performance[category]['completed'] + 1
        s0 = performance[category]['score']
        s = (score + performance[category]['score']*c)/c
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
            for problem_history in self.problems_history
            if (set(Problem.query.get_or_404(problem_history.problem_id).label_names()) & set(categories)) and problem_history.last_attempted
        ]
        # return [in_category.order_by(ProblemHistory.last_attempted.desc()).limit(n)]
        # return max(in_category,key=attrgetter('last_attempted'))
        return sorted(in_category, key=attrgetter('last_attempted'))[:n]
    def total_completed(self):
        return self.problems_history.filter_by(completion=1).count()

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
        email = request.form.get('email')
        username_exists = db.session.execute(db.select(User).where(User.username == username)).first()
        email_exists = db.session.execute(db.select(User).where(User.email == email)).first()

        errors = []
        if username_exists:
            errors.append('username_exists')
        if email_exists:
            errors.append('email_exists')
        if not validate_email.check(email):
            errors.append('invalid_email')

        if not errors:
            user = User(email=request.form.get('email'),
                        username=request.form.get('username'),
                        password=request.form.get('password'))
            default_profile = Profile(name = f"{request.form.get('username')} default", 
                                      user_id = current_user.id,
                                      performance = str({category : {"score":50.0,"status":0,"completed":0} for category in AllStatistics.query.first().category_names()}),
                                      preferred_categories = json.dumps(AllStatistics.query.first().category_names()),
                                      date_created = datetime.now(),
                                      last_active = datetime.now())
            db.session.add(user)
            db.session.add(default_profile)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return render_template('register.html',errors=errors)
    return render_template('register.html',errors=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if validate_email.check(request.form.get('identifier')):
            user = User.query.filter_by(
                email=request.form.get('identifier')).first()
        else:
            user = User.query.filter_by(
                username=request.form.get('identifier')).first()
        if user and user.password == request.form.get('password'):
                login_user(user)
                return redirect(url_for('index'))
        else:
            return render_template('login.html',user_not_found=True)
    return render_template('login.html',user_not_found=False)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'change_profile' in request.form:
            new_profile = request.form['profile_choices']
            current_user.current_profile = new_profile
            db.session.commit()
        else:
            profile_name = request.form.get('profile_name')
            new_profile = Profile(name = profile_name, 
                                  user_id = current_user.id,
                                  performance = str({category : {"score":50.0,"status":0,"completed":0} for category in AllStatistics.query.first().category_names()}),
                                  preferred_categories = json.dumps(AllStatistics.query.first().category_names()),
                                  date_created = datetime.now(),
                                  last_active = datetime.now())
            db.session.add(new_profile)
            db.session.commit()
    return render_template('profile.html', profiles=current_user.profiles, current_profile=current_user.current_profile)

@app.route('/')
@login_required
def index():
    try:
        problem_id = current_user._current_profile().problems_history.order_by(ProblemHistory.id.desc()).limit(1)[0].problem_id
    except Exception:
        problem_id = 1
    return redirect(f'/problems/{problem_id}')

@app.route('/problems/<int:problem_id>', methods=['GET','POST'])
@login_required
def render(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    if not current_user._current_profile().problems_history.filter_by(problem_id=problem_id).first():
        db.session.add(ProblemHistory(problem_id=problem_id, profile_id=current_user.current_profile))
        db.session.commit()
    problem_history = current_user._current_profile().problems_history.filter_by(problem_id=problem_id).first()

    # Updating preferred categories
    if request.method == 'POST' and 'categories' in request.form:
        current_user._current_profile().preferred_categories = json.dumps(request.form.getlist('categories'))
        db.session.commit()
    else:
        if request.method == 'POST' and problem_history.completion == 0:
            with contextlib.suppress(werkzeug.exceptions.BadRequestKeyError):
                answer = request.form['choices']
                problem_history.append_answer(answer)
                if answer == problem.answer:
                    problem_history.completion = 1
                db.session.commit()
        if request.method == 'POST' and request.form.get("Next Problem"):
            return redirect(url_for('next_problem', ph_id = problem_history.id))

    return render_template('display_problems.html',
                    choices=['A','B','C','D','E'],
                    problem=problem,
                    problem_history=problem_history,
                    allstatistics=AllStatistics.query.first(),
                    profile=current_user._current_profile())

@app.route('/next_problem/<int:ph_id>')
@login_required
def next_problem(ph_id):
    problem_history = current_user._current_profile().problems_history.filter_by(id=ph_id).first()
    problem = Problem.query.get_or_404(problem_history.problem_id)
    labels = problem._labels()
    problem_score = (5-problem_history.attempts)*25 * (1 + (problem.difficulty - 1)*.25)
    
    for label in label_to_categories(labels):
        current_user._current_profile().update_cat_score(label,problem_score)
        current_user._current_profile().update_cat_completion(label)
        db.session.commit()
    
    return redirect(url_for('recommend_problem'))

@app.route('/recommend')
@login_required
def recommend_problem():
    # picks category based on weighted probability and non-mastery
    categories = []
    scores = []
    for category in current_user._current_profile()._performance():
        if current_user._current_profile()._performance()[category]['status'] < 3 and category in current_user._current_profile()._preferred_categories():
            categories.append(category)
            scores.append(current_user._current_profile()._performance()[category]['score'])
    if not max(scores):
        weights = [1 for _ in scores]
    else:
        # Makes weights the distance between a score and twice the greatest score (adjusted as percentages)
        weights = [2-float(score)/max(scores) for score in scores]
    category = random.choices(categories,weights)[0]

    # Picks a problem with difficulty matching the status
    last_attempted = current_user._current_profile().get_last_attempted(1,category)

    if last_attempted:
        last_completed_difficulty = Problem.query.get_or_404(last_attempted[0].problem_id).difficulty
        match current_user._current_profile()._performance()[category]['status']:
            case 1:
                difficulty = last_completed_difficulty - 1 if last_completed_difficulty > 1 else 1
            case 2:
                difficulty = last_completed_difficulty + 1 if last_completed_difficulty < 5 else 5
    else:
        difficulty = 3
    next_problem_id = query_problems(category, difficulty=difficulty)

    return redirect(url_for('render', problem_id = next_problem_id))

def query_problems(category, difficulty=3, approx_difficulty=True, allow_completed=True):
    """
    Returns the id of a problem with the given category
    approx_difficulty: if none with the given difficulty could be found, one of the closest difficulty will be used
    allow_completed: if none incompleted could be found, one that is completed will be picked
    """
    # filter_difficulties = lambda x : Problem.query.filter(Problem.in_category(category),
    #                                                       Problem.difficulty in x,
    #                                                       current_user.current_profile.problems_history.filter_by(problem_id=Problem.id).first().attempts > 0).all()
    filter_difficulties = lambda x : [problem for problem in Problem.query.all() 
                                      if problem.in_category(category) 
                                      and problem.difficulty in x 
                                      and (not current_user._current_profile().problems_history.filter_by(problem_id=problem.id).first() 
                                           or not current_user._current_profile().problems_history.filter_by(problem_id=problem.id).first().completion)]
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