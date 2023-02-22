import requests
from bs4 import BeautifulSoup as bs
import json

base_url = "https://artofproblemsolving.com/wiki/index.php/"
headers = {
    "User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9" 
}

def get_content(url):
    content = requests.get(url,headers).content
    soup = bs(content, 'html5lib')
    return soup

def get_problem(year,level,instance,number):
    problem_url = f"{base_url}{year}_AMC_{level}{instance}_Problems/Problem_{number}"
    soup = get_content(problem_url)

    problem_header = soup.find_all("h2")[1]
    
    sibling = problem_header.find_next_sibling()
    problem_p_concat = ""
    while sibling.name != "h2":
        problem_p_concat += str(sibling)
        sibling = sibling.find_next_sibling()
    problem_content = bs(problem_p_concat, 'html5lib')
    
    choices = problem_content.find_all(attrs="latex")[-1].extract()
    return problem_content,choices

def get_answer(year,level,instance,number):
    key_url = f"{base_url}{year}_AMC_{level}{instance}_Answer_Key"
    soup = get_content(key_url)
    answer_list = soup.find_all("li")
    return answer_list[number-1].string
    
def test_gather():
    test_json = {}

    year = 2022
    level = 10
    instance = "A"

    for problem_number in range (1,26):
        id = f"{year} AMC {level}{instance} #{problem_number}"
        
        test = year,level,instance
        problem, choices = get_problem(year,level,instance,problem_number)
        answer = get_answer(year,level,instance,problem_number)

        dict = {
            "test": test,
            "problem": str(problem),
            "choices": str(choices),
            "answer": answer
        }

        test_json.update({id:dict})
        print(problem_number)

        json.dump(test_json, open("test.json","r+"), indent=4)

if __name__ == "__main__":
    print(test_gather())
