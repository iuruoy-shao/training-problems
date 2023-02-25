var problemDiv = document.getElementById("problem_display");
var problemHeader = document.getElementById("problem_header");
var choices = ["A","B","C","D","E"]

function loadProblem(key) {
    fetch('/test.json')
        .then((result) => result.json())
        .then(
            function (problemsJson) {
                problemContent = problemsJson[key].problem
                answerChoices = problemsJson[key].choices
                correctAnswer = problemsJson[key].answerChoices

                problemContentSliced = problemContent.slice(6,problemContent.length-7);
                problemDiv.innerHTML = problemContentSliced;
                problemHeader.innerHTML = key;
                
                for (let i = 0; i < 5; i++) {
                    let letter = choices[i]
                    let choiceDiv = document.getElementById(letter);
                    choiceDiv.innerHTML += `<button>${letter}</button>`
                    choiceDiv.innerHTML += `<div class="latex">$${answerChoices[i]}$</div>`
                }
            }
        )
}

function testProblemToKey(test,problem) {
}

loadProblem("2022 AMC 10A #5");