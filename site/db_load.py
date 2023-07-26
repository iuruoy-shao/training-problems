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
            answer = problems[problem]['answer'],
            solutions = json.dumps(problems[problem]['solutions']),
            difficulty = json.dumps(
                1 if problems[problem]['number'] <= 5
                else 2 if problems[problem]['number'] <= 10
                else 3 if problems[problem]['number'] <= 15
                else 4 if problems[problem]['number'] <= 20
                else 5
            )
        )
        db.session.add(problem_to_add)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_from_json('amc_10_problems_with_sol.json')
        db.session.commit()