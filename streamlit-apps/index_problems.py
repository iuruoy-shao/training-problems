import streamlit as st
import numpy as np
import pandas as pd
import torch
import json
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gather_problems import base_url
from transformers import DistilBertTokenizer, DistilBertModel
from huggingface_hub import hf_hub_download
import nltk
from nltk.corpus import stopwords

from io import StringIO
from html.parser import HTMLParser
from bs4 import BeautifulSoup

nltk.download('stopwords')
nltk_stopwords = set(stopwords.words('english'))

REPO_ID = 'iuruoy-shao/top-level-with-solutions-distilbert-amc10-2019-2022'
FILENAME = 'top-level-with-solutions-distilbert-amc10-2019-2022.pt'

class DistilBERTClass(torch.nn.Module):
    def __init__(self, num_classes):
        super(DistilBERTClass, self).__init__()
        self.l1 = DistilBertModel.from_pretrained("distilbert-base-uncased")
        self.pre_classifier = torch.nn.Linear(768, 768)
        self.dropout = torch.nn.Dropout(0.3)
        self.classifier = torch.nn.Linear(768, num_classes)

    def forward(self, input_ids, attention_mask):
        output_1 = self.l1(input_ids=input_ids, attention_mask=attention_mask)
        hidden_state = output_1[0]
        pooler = hidden_state[:, 0]
        pooler = self.pre_classifier(pooler)
        pooler = torch.nn.ReLU()(pooler)
        pooler = self.dropout(pooler)
        return self.classifier(pooler)
    
st.set_page_config(page_title="Categorizing AMC Problems",
                   menu_items={"About":"""This is a demonstration of our top-level categorization model for competition math problems at the highschool level.
                               The model can be found at https://huggingface.co/iuruoy-shao/top-level-with-solutions-distilbert-amc10-2019-2022."""})

problems_data = json.load(open(Path(__file__).parent.parent / 'amc_10_problems_with_sol.json'))
categories = ['Miscellaneous', 'Algebra', 'Geometry', 'Number Theory', 'Counting and Probability']
device = torch.device("cpu")

model = DistilBERTClass(num_classes=5)
model.to(device)
model = torch.load(hf_hub_download(repo_id=REPO_ID,filename=FILENAME))

tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased',truncation_side='left',truncation=True,max_length=256,pad_to_max_length=True,add_special_tokens=True)
tokenizer.add_tokens(list(open(Path(__file__).parent.parent / 'latex-vocabulary/latex_symbols.txt','r')))

def make_prediction(sequence):
    problem_input = tokenizer.encode_plus(
        strip_problem_html(sequence),
        None,
        add_special_tokens=True,
        max_length=256,
        pad_to_max_length=True,
        return_tensors="pt").to(device)
    
    outputs = []
    outputs.extend(torch.sigmoid(model(**problem_input)).cpu().detach().numpy().tolist())
    outputs = np.array(outputs) >= 0.5
    
    return [[1 if value else 0 for value in output] for output in outputs]

problem, results = st.columns(2,gap='large')

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def get_latex_from_alt(context):
    strip_deliminators = lambda latex: latex.replace('$','').replace('\\[','').replace('\\]','')

    context_soup = BeautifulSoup(context)
    latex_images = context_soup.find_all('img')
    for image in latex_images:
        image.replace_with(strip_deliminators(image['alt']))
    # return [strip_deliminators(image['alt']) for image in latex_images]
    return str(context_soup)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def remove_stopwords(text):
    filtered_text = [w for w in text.split() if w.lower() not in nltk_stopwords]
    return " ".join(filtered_text)

strip_problem_html = lambda x: strip_tags(get_latex_from_alt(x))

with problem:
    st.title("Categorize AMC Problems")

    tests = [[year,10,instance] for year in [2015, 2016, 2017, 2018, 2019, 2020, 2021, "2021_Fall", 2022] for instance in ["A","B"]][::-1]
    tests_display = [f"{test[0]} AMC 10{test[2]}".replace("_"," ") for test in tests]

    test_index = tests_display.index(st.selectbox(label="Test", options=tests_display, index=17))
    test = tests[test_index]
    problem_number = st.selectbox(label="Problem Number", 
                                  index=15,
                                  options=[problems_data[problem]['number'] for problem in problems_data 
                                           if problems_data[problem]['test'] == test])

    problem = f'{tests_display[test_index]} #{problem_number}'.replace(" Fall","_Fall")
    problem_content = problems_data[problem]['problem']
    solutions_text = strip_tags(get_latex_from_alt(" ".join([solution for solution in problems_data[problem]["solutions"] if 'http' not in solution])))
    choices_text = " ".join(problems_data[problem]["choices"])
    combined_text = remove_stopwords(" ".join([problem_content, solutions_text, choices_text]))
    st.write(f"[View problem on AoPS]({base_url}{tests_display[test_index].replace(' ','_')}_Problems/Problem_{problem_number})")
    st.components.v1.html(problem_content,height=250,scrolling=True)
    categorize = st.button(label="Categorize")

with results:
    if categorize:
        st.caption("""Note: data was trained on problems after 2018
             ––those will have predictions of greater accuracy.
             """)
        predictions = make_prediction(problem_content)[0]
        labels = pd.Series(data=predictions,
                           index=["Miscellaneous","Algebra","Geometry","Number Theory","Counting & Probability"],
                           name='Label')
        st.dataframe(labels,use_container_width=True)