from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# test - tuple
# problem - html string
# choices - latex

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test = db.Column(db.String, nullable=False)
    choices = db.Column(db.ARRAY, nullable=False)
    

    problem_content = db.Column(db.String())


    def __init__(test,problem_number,problem,choices,answer,self):
        self.test = test
        self.problem_number = problem_number
        self.problem = problem
        self.choices = choices
        self.answer = answer

    def __str__(self):
        pass
    
    def check_problem(choice,self):
        return choice == self.answer

@app.route('/')
def index():
    return render_template('index.html', choices=['A','B','C','D','E'])


if __name__ == '__main__':
    app.run(port=8000,debug=True)