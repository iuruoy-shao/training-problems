from app import db, Problem, AllStatistics, app

import json
import pandas as pd

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
                1 if problems[problem]['number'] <= 10
                else 2 if problems[problem]['number'] <= 20
                else 3
            ),
            labels = json.dumps(get_label(problem)))
        db.session.add(problem_to_add)

def load_hand_labeled():
    misc_labels = (4,23)
    alg_labels = (23,44)
    geo_labels = (44,60)
    nt_labels = (60,68)
    cb_labels = (68,85)

    labeled_data = pd.read_csv('../problem_labels.csv').replace([True,False],[1,0])

    def extract_labels(cols):
            start, end = cols
            return labeled_data[labeled_data.columns[start:end]].values.tolist()

    labeled_data['misc-labels'] = extract_labels(misc_labels)
    labeled_data['alg-labels'] = extract_labels(alg_labels)
    labeled_data['geo-labels'] = extract_labels(geo_labels)
    labeled_data['nt-labels'] = extract_labels(nt_labels)
    labeled_data['cb-labels'] = extract_labels(cb_labels)
    labeled_data['Miscellaneous'] = labeled_data['misc-labels'].apply(lambda x: int(any(x)))
    labeled_data['Combinatorics'] = labeled_data['cb-labels'].apply(lambda x: int(any(x)))
    labeled_data['tl-labels'] = labeled_data[['Miscellaneous','Algebra','Geometry','Number Theory','Combinatorics']].values.tolist()

def get_label(problem):
    with open('problem-classification/outputs_file_8.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.find(problem) != -1:
                print(line.strip('\n')[-15:])
                return json.loads(line.strip('\n')[-15:])

if __name__ == "__main__":
    with app.app_context():
        load_from_json('problem-classification/amc_8_problems_with_sol.json')
        print("loaded")
        db.session.commit()
        print("committed 1")
        db.get_or_404(AllStatistics, 1).update_counts()
        db.session.commit()
        print("committed 2")