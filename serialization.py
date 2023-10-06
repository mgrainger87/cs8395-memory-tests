from base_types import *
import os
import pathlib

def get_problems_json(basePath: str):
	problemsJSON = {}
	problemsDirectory = os.path.join(basePath, "problems")
	for problem_file in [file for file in sorted(os.listdir(problemsDirectory)) if not file.startswith('.')]:
		problemPath = os.path.join(problemsDirectory, problem_file)
		with open(problemPath) as f:
			problemJSON = json.loads(f.read())
		problemsJSON[problem_file] = problemJSON
	return problemsJSON		

def get_problems(basePath: str):
	return [ProblemDefinition.from_json(x) for x in get_problems_json(basePath).values()]

def save_solution(basePath: str, solution: LLMSolution):
	directoryPath = os.path.join(basePath, "solutions", solution.model_identifier, solution.problem_identifier)
	pathlib.Path(directoryPath).mkdir(parents=True, exist_ok=True)
	path = os.path.join(directoryPath, solution.prompt_identifier + ".json")
	
	# print(path)
	with open(path, 'w') as f:
		jsonString = json.dumps(solution.to_json(), indent=4)
		f.write(jsonString)

def get_solutions(basePath: str, model_identifier: str):
	solutions = []
	solutionsDirectory = os.path.join(basePath, "solutions", model_identifier)

	if os.path.exists(solutionsDirectory):
		for problemName in [file for file in sorted(os.listdir(solutionsDirectory)) if not file.startswith('.')]:
			problemDirectory = os.path.join(solutionsDirectory, problemName)
	
			for solution_file in [file for file in sorted(os.listdir(problemDirectory)) if not file.startswith('.')]:
				solutionPath = os.path.join(problemDirectory, solution_file)
				# print(solutionPath)
				with open(solutionPath) as f:
					solutionJSON = json.loads(f.read())
				solutions.append(LLMSolution.from_json(solutionJSON))
	return solutions		


def update_report(basePath: str, grades: GradingOutput, solutionGrade: SolutionGrade, current_report_path: str):
	if os.path.exists(current_report_path):
			with open(current_report_path, 'r') as f:
				report = json.load(f)
	else:
		report = {
			"Problem Sets": {},
			"Average Scores Per Problem Set": {},
			"Average Scores Per Criterion": {}
		}

	problem_set_name = basePath
	if problem_set_name not in report["Problem Sets"]:
		report["Problem Sets"][problem_set_name] = {}
	if grades.grader_identifier not in report["Problem Sets"][problem_set_name]:
		report["Problem Sets"][problem_set_name][grades.grader_identifier] = []

	report["Problem Sets"][problem_set_name][grades.grader_identifier].append(solutionGrade.to_json())

	# update average score for problem set
	all_scores = [problem["score"] for grader in report["Problem Sets"][problem_set_name].values() for problem in grader]
	avg_score = sum(all_scores) / len(all_scores)
	report["Average Scores Per Problem Set"][problem_set_name] = avg_score

	# update average score for grading metric
	all_scores_for_grader = [problem["score"] for pset in report["Problem Sets"].values() for problem in pset.get(grades.grader_identifier, [])]
	avg_score_for_grader = sum(all_scores_for_grader) / len(all_scores_for_grader) if all_scores_for_grader else 0
	report["Average Scores Per Criterion"][grades.grader_identifier] = avg_score_for_grader
    
	pathlib.Path(os.path.dirname(current_report_path)).mkdir(parents=True, exist_ok=True)
	with open(current_report_path, 'w') as f:
		json.dump(report, f, indent=4)	


	
def save_grades(basePath: str, grades: GradingOutput, current_report_path: str):
	# print(grades.solution_grades)
	for solutionGrade in grades.solution_grades:
		directoryPath = os.path.join(basePath, "grades", solutionGrade.model_identifier, grades.grader_identifier, solutionGrade.problem_identifier)
		pathlib.Path(directoryPath).mkdir(parents=True, exist_ok=True)
		path = os.path.join(directoryPath, solutionGrade.prompt_identifier + ".json")

		# print(path)
		with open(path, 'w') as f:
			jsonString = json.dumps(solutionGrade.to_json(), indent=4)
			f.write(jsonString)
		
		update_report(basePath, grades, solutionGrade, current_report_path)
		
			
def get_grades(basePath: str, model_identifier: str, grader_identifier: str):
	grades = []
	gradesDirectory = os.path.join(basePath, "grades", model_identifier, grader_identifier)
	
	for problemName in [file for file in sorted(os.listdir(gradesDirectory)) if not file.startswith('.')]:
		problemDirectory = os.path.join(gradesDirectory, problemName)
	
		for grade_file in [file for file in sorted(os.listdir(problemDirectory)) if not file.startswith('.')]:
			gradePath = os.path.join(problemDirectory, grade_file)
			# print(gradePath)
			with open(gradePath) as f:
				gradeJSON = json.loads(f.read())
			grades.append(SolutionGrade.from_json(gradeJSON))
	return GradingOutput(grades, grader_identifier)		
