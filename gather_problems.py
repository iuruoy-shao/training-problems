import requests
from bs4 import BeautifulSoup as bs
import json

base_url = "https://artofproblemsolving.com/wiki/index.php/"
headers = {
    "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9" 
}
letter_choices = ["A","B","C","D","E"]

def get_content(url):
    content = requests.get(url,headers).content
    return bs(content, 'html5lib')

def get_problem(year,level,instance,number):
    problem_url = f"{base_url}{year}_AMC_{level}{instance}_Problems/Problem_{number}"
    soup = get_content(problem_url)

    problem_headers = soup.find_all(name="h2")
    problem_header = [header for header in problem_headers 
                    for string in header.strings
                    if "Problem" in string][0]
    
    sibling = problem_header.find_next_sibling()
    problem_p_concat = ""
    while sibling.name != "h2":
        problem_p_concat += str(sibling)
        sibling = sibling.find_next_sibling()
    problem_content = bs(problem_p_concat, 'html5lib')
    
    latex_tags = problem_content.find_all(attrs="latex")

    choices = []
    choices_contains_latex = True
    for tag in latex_tags:
        contains_choice = False
        alt = tag["alt"]
        contains_choice = any([f"({char})" in alt for char in letter_choices]
                              +["\\textbf{"+char in alt or "\textbf{"+char in alt
                                for char in letter_choices])
        
        if contains_choice:
            if tag.next_sibing:
                choices.append(tag.next_sibling)
                choices_contains_latex = False
            else:
                choices.append(alt)
            tag.extract()

    # choices = problem_content.find_all(attrs="latex")[-1].extract()["alt"]

    if len(choices) == 1:
        choices = dissect_choices(choices[0])
    if choices_contains_latex:
        cleanup_choices(choices)
    return problem_content,choices

def get_answer(year,level,instance,number):
    key_url = f"{base_url}{year}_AMC_{level}{instance}_Answer_Key"
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

        choice = choice.replace(char+")}\\","")
        choice = choice.replace(char+") }\\","")
        choice = choice.replace(char+") }","")
        choice = choice.replace(char+")}","")
        choice = choice.replace(char+")","")
        choice = choice.replace(char+"})","")
        choice = choice.replace(char+"} )","")
        choice = choice.replace("(","")
        choice = choice.replace("\\textbf{","")
        choice = choice.replace("\\:","")
        choice = choice.replace(":","")

        split_list[i] = choice
    return split_list
    
def gather_year(year,level,instance,json_file="amc_10_problems.json"):
    try:
        problems_json = json.load(open(json_file,"r+"))
    except:
        problems_json = {}

    for problem_number in range (1,26):
        gather_problem(year,level,instance,problem_number,problems_json)
        json.dump(problems_json, open(json_file,"r+"), indent=4)

def gather_problem(year,level,instance,problem_number,loading_json):
    id = f"{year} AMC {level}{instance} #{problem_number}"
    
    test = year,level,instance
    try:
        problem, choices = get_problem(year,level,instance,problem_number)
    except:
        problem = ""
        choices = []
    answer = get_answer(year,level,instance,problem_number)

    dict = {
        "test": test,
        "problem": str(problem),
        "choices": choices,
        "answer": answer
    }

    loading_json.update({id:dict})

    if problem == "":
        print("Problem location error:",id)
    elif len(choices) != 5:
        print("Choice error:",id)

if __name__ == "__main__":
    for i in range(2015,2021):
        gather_year(i,10,"A")
        gather_year(i,10,"B")
    gather_year(2021,10,"A")
    gather_year(2021,10,"B")
    gather_year("2021_Fall",10,"A")
    gather_year("2021_Fall",10,"B")
    gather_year(2022,10,"A")
    gather_year(2022,10,"B")