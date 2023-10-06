import sys
import json

from llm_test_helpers import get_args
from suite_helper import *

if __name__ == "__main__":
	args = get_args(sys.argv)
	model_identifier = args.model
	
	base_path="problem_sets/memory"
	problem_definitions = load_problems_definitions(base_path)
	
	print("Grading solutions…")
	grading_output = grade_solutions(base_path, problem_definitions, model_identifier, "memory")
	print(grading_output)
	
	percentage_score = grading_output.overall_score * 100
	
	# Write the data to the specified file as JSON
	with open("output.json", "w") as file:
		json.dump({"output": percentage_score}, file)
