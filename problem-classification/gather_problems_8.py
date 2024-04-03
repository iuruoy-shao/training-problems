import requests
from bs4 import BeautifulSoup as bs
import json

JSON_FILE_OUTPUT = 'amc_8_problems_with_sol.json'

base_url = "https://artofproblemsolving.com/wiki/index.php/"
headers = {
    "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9" 
}

letter_choices = ['A','B','C','D','E']

def get_content(url):
    content = requests.get(url,headers).content
    return bs(content, "html5lib")

def get_problem(year,level,number):
    problem_url = f'{base_url}{year}_AMC_{level}_Problems/Problem_{number}'
    soup = get_content(problem_url)

    #find potential overlap
    overlap_header = soup.find_all(name='dd') or "none"
    if(overlap_header!="none"):
        return "","",""
    problem_headers = soup.find_all(name='h2')
    problem_header = [header for header in problem_headers 
                      for string in header.strings
                      if 'Problem' in string][0]
    solution_headers = [header for header in problem_headers 
                        for string in header.strings
                        if 'Solution' in string]
    
    # Get problem text
    sibling = problem_header.find_next_sibling()
    problem_p_concat = ""
    while sibling.name != 'h2':
        problem_p_concat += str(sibling)
        sibling = sibling.find_next_sibling()
    problem_content = bs(problem_p_concat, 'html5lib')

    # Get solutions text
    solutions_p = []
    for solution_header in solution_headers:
        solution = ""
        sibling = solution_header.find_next_sibling()
        while sibling and sibling.name != 'h2':
            if sibling.name == 'p':
                solution += str(sibling)
            sibling = sibling.find_next_sibling()
        solutions_p.append(solution)
    
    latex_tags = problem_content.find_all(attrs='latex')

    choices = []
    choices_contains_latex = True
    for tag in reversed(latex_tags):
        contains_choice = False
        alt = tag['alt']
        contains_choice = any([f"({char})" in alt for char in letter_choices]
                              +["\\textbf{"+char in alt or "\textbf{"+char in alt
                                for char in letter_choices])
        if len(choices)==5:
            break
        if contains_choice:
            if tag.next_sibing:
                choices.insert(0,tag.next_sibling)
                choices_contains_latex = False
            else:
                choices.insert(0,alt)
            tag.extract()

    # choices = problem_content.find_all(attrs="latex")[-1].extract()["alt"]
    try:
        if len(choices) == 2:
            choices.pop(0)
        if len(choices) == 1:
            choices = dissect_choices(choices[0])
        if choices_contains_latex:
            cleanup_choices(choices)
    except Exception:
        choices = []
    return problem_content,choices,solutions_p

def get_answer(year,level,number):
    key_url = f'{base_url}{year}_AMC_{level}_Answer_Key'
    soup = get_content(key_url)
    answer_list = soup.find_all("li")
    return answer_list[number-1].string

def dissect_choices(choices):
    choices = choices[choices.find("$")+1:choices.rfind("$")]
    choices = choices.replace("\\qquad","")
    split_list = choices.split("\\textbf{" if "\\textbf{" in choices else "\textbf{")

    try:
        split_list.remove("")
    except:
        pass
    try:
        split_list.remove("(")
    except:
        pass

    return split_list
   
def cleanup_choices(split_list):
    for i in range(len(split_list)):
        choice = split_list[i]
        char = letter_choices[i]

        to_replace = [char+") }",
                      char+")}",
                      char+")",
                      char+"})",
                      char+"} )",
                      "(",
                      "\\textbf{",
                      "\\:",
                      "\\:",
                      ":"
                    ]

        for s in to_replace:
            choice = choice.replace(s,"")

        split_list[i] = choice
    return split_list

def gather_problem(year,level,problem_number,loading_json):
    problem_id = f"{year} AMC {level} #{problem_number}"
    test = year,level
    problem, choices, solutions = get_problem(year,level,problem_number)
    answer = get_answer(year,level,problem_number)

    test_details = {
        "test": test,
        "number": problem_number,
        "problem": str(problem),
        "choices": choices,
        "answer": answer,
        "solutions": solutions
    }

    if not problem:
        print("Problem location:",problem_id)
    elif len(choices) != 5:
        print("Choice error:",problem_id)
    elif len(solutions) < 1:
        print("No solutions found:",problem_id)
    if problem and (len(choices) == 5):
        loading_json.update({problem_id:test_details})
    
def gather_test(year,level,json_file=JSON_FILE_OUTPUT):
    try:
        problems_json = json.load(open(json_file,"r+"))
    except:
        problems_json = {}

    for problem_number in range (1,26):
        gather_problem(year,level,problem_number,problems_json)
        json.dump(problems_json, open(json_file,"r+"), indent=4)

if __name__ == "__main__":
    for year in range(2015,2021):
        gather_test(year,8,json_file=JSON_FILE_OUTPUT)
    for year in range(2022,2025):
        gather_test(year,8,json_file=JSON_FILE_OUTPUT)