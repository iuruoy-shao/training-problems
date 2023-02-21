# test - tuple
# problem - html string
# choices - latex

class Problem:
    types = []

    def __init__(test,problem_number,problem,choices,answer,self):
        self.test = test
        self.problem_number = problem_number
        self.problem = problem
        self.choices = choices
        self.answer = answer

    def __str__():
        pass

    def check_problem(choice,self):
        return choice == self.answer