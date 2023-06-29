from app import db, Problem, app

import json

def load_from_json(file_name):
    problems = json.load(open(file_name))
    
    for problem in problems:
        problem_to_add = Problem(
            test = json.dumps(problems[problem]['test']),
            number = problems[problem]['number'],
            problem_content = problems[problem]['problem'],
            choices = json.dumps(problems[problem]['choices']),
            answer = json.dumps(problems[problem]['answer'])
        )
        db.session.add(problem_to_add)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_from_json('../amc_10_problems.json')
        db.session.commit()