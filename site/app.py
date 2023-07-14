from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'amc10_problems.db')
db = SQLAlchemy(app)
with app.app_context():
    db.create_all()

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test = db.Column(db.String, nullable=False)
    number = db.Column(db.Integer)
    choices = db.Column(db.String)
    problem_content = db.Column(db.String(), nullable=False)
    answer = db.Column(db.String, nullable=False)
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

@app.route('/')
def index():
    return redirect('/problems/1')

@app.route('/problems/<int:problem_id>', methods=['GET','POST'])
def render(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    try:
        problem_history = db.session.execute(db.select(ProblemHistory).where(ProblemHistory.problem_id == problem_id)).first()[0]
    except Exception:
        db.session.add(ProblemHistory(problem_id=problem_id))
        db.session.commit()
        problem_history = db.session.execute(db.select(ProblemHistory).where(ProblemHistory.problem_id == problem_id)).first()[0]

    if request.method == 'POST' and problem_history.completion == 0:
        problem_history.last_attempted = datetime.now()
        problem_history.attempts += 1

        answer = request.form['choices']
        problem_history.append_answer(answer)
        if answer == problem.answer:
            problem_history.completion = 1
        db.session.commit()
        return render_template('display_problems.html',
                        choices=['A','B','C','D','E'],
                        problem=problem,
                        problem_history=problem_history)
    else:
        return render_template('display_problems.html',
                        choices=['A','B','C','D','E'],
                        problem=problem,
                        problem_history=problem_history)

if __name__ == '__main__':
    app.run(port=8000,debug=True)