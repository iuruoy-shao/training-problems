from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
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

    def __repr__(self):
        # return f'{self.AMC_name} Number {self.number}'
        return f'{self.test} Number {self.number}'
    
    def AMC_name(self):
        return f'{self._test[0]} AMC {self._test[1]}{self._test[2]}'
    def _test(self):
        return json.loads(self.test)
    def _choices(self):
        return json.loads(self.choices)
    def _labels(self):
        return json.loads(self.labels)

@app.route('/')
def index():
    return redirect('/problems/1')

@app.route('/problems/<int:problem_id>', methods=['GET','POST'])
def render(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    return render_template('display_problems.html',
                    choices=['A','B','C','D','E'],
                    problem=problem)

if __name__ == '__main__':
    app.run(port=8000,debug=True)