from langchain.llms import OpenAI

import sys
import serialization
import re

from llm_test_helpers import get_llm, get_args
from suite_helper import *

if __name__ == "__main__":
	args = get_args(sys.argv)
	model_identifier = args.model
	llm = get_llm(model_identifier)
	
	base_path="problem_sets/memory"
	problem_definitions = load_problems_definitions(base_path)
	
	print("Generating solutions…")
	generate_solutions(base_path, problem_definitions, model_identifier, llm)
