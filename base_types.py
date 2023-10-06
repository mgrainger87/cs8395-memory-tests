from typing import Dict, List, Union, Optional, Any
import ast
import json
import re

# Define necessary types
ProblemID = str
AIIdentifier = str
Code = str
Feedback = str
Score = int
SubCriteriaScores = Dict[str, Score]
IssueCategory = str
IssueDescription = str
Issue = Dict[IssueCategory, IssueDescription]
Tag = str

class LLMSolution:
	"""
	Represents the solution output from an AI model.
	"""
	def __init__(self,
				 problem_identifier: str,
				 model_identifier: str,
				 prompt_identifier: str,
				 solution_code: str,
				 feedback: Optional[dict] = None):
		self.problem_identifier = problem_identifier
		self.model_identifier = model_identifier
		self.prompt_identifier = prompt_identifier
		self.solution_code = solution_code
		self.feedback = feedback

	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'LLMSolution':
		"""Create an LLMSolution instance from JSON data."""
		return cls(
			problem_identifier=data.get('problem_identifier', ''),
			model_identifier=data.get('model_identifier', ''),
			prompt_identifier=data.get('prompt_identifier', ''),
			solution_code=data.get('solution_code', ''),
			feedback=data.get('feedback', None)
		)
		
	def to_json(self) -> Dict[str, Any]:
		"""Convert the LLMSolution instance to a JSON-serializable dictionary."""
		return {
			'problem_identifier': self.problem_identifier,
			'model_identifier': self.model_identifier,
			'prompt_identifier': self.prompt_identifier,
			'solution_code': self.solution_code,
			'feedback': self.feedback
		}

	def __str__(self) -> str:
		feedback_str = f", feedback={self.feedback}" if self.feedback else ""
		return (
			f"LLMSolution("
			f"problem_identifier={self.problem_identifier}, "
			f"model_identifier={self.model_identifier}, "
			f"prompt_identifier={self.prompt_identifier}"
			f"solution_code={self.solution_code}, "
			f"{feedback_str}"
			f")"
		)

class Issue:
		def __init__(self,
					 issue_category: str,
					 issue_description: str):
			self.issue_category = issue_category
			self.issue_description = issue_description
		
		@classmethod
		def from_json(cls, data: Dict[str, Any]) -> 'Issue':
			"""Create an Issue instance from JSON data."""
			issue_category = data.get('issue_category', '')
			issue_description = data.get('issue_description', '')
			return cls(issue_category, issue_description)
		
		def to_json(self) -> Dict[str, Any]:
			"""Convert the Issue instance to a JSON-serializable dictionary."""
			return {
				'issue_category': self.issue_category,
				'issue_description': self.issue_description
			}
		
		def __str__(self) -> str:
			return f"Issue({self.issue_category}, {self.issue_description})"

class SolutionGrade:
	"""
	Represents the grade for a single solution.
	"""
	def __init__(self,
				 problem_identifier: str,
				 prompt_identifier: str,
				 model_identifier: str,
				 score: float,
				 sub_criteria_scores: Optional[dict] = None,
				 issues: Optional[List[str]] = None):
		self.problem_identifier = problem_identifier
		self.prompt_identifier = prompt_identifier
		self.score = score
		self.model_identifier = model_identifier
		self.sub_criteria_scores = sub_criteria_scores
		self.issues = issues

	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'SolutionGrade':
		"""Create a SolutionGrade instance from JSON data."""
		problem_identifier = data.get('problem_identifier', '')
		prompt_identifier = data.get('prompt_identifier', '')
		model_identifier = data.get('model_identifier', '')
		score = data.get('score', 0)
		sub_criteria_scores = data.get('sub_criteria_scores', None)
		issues = data.get('issues', [])
		return cls(problem_identifier, prompt_identifier, model_identifier, score, sub_criteria_scores, issues)
	
	def to_json(self) -> Dict[str, Any]:
		"""Convert the SolutionGrade instance to a JSON-serializable dictionary."""
		return {
			'problem_identifier': self.problem_identifier,
			'prompt_identifier': self.prompt_identifier,
			'model_identifier': self.model_identifier,
			'score': self.score,
			'sub_criteria_scores': self.sub_criteria_scores,
			'issues': self.issues
		}
	
	def __str__(self) -> str:
		sub_criteria_scores_str = (
			f"Sub Criteria Scores: {self.sub_criteria_scores}"
			if self.sub_criteria_scores
			else "No Sub Criteria Scores"
		)
		
		issues_separator = "\n\t"
		issues_str = (
			f"Issues: [\n\t{issues_separator.join(str(issue) for issue in self.issues)}]"
			if self.issues
			else "No Issues"
		)
		return (
			f"SolutionGrade:\n"
			f"  Problem Identifier: {self.problem_identifier}\n"
			f"  Prompt Identifier: {self.prompt_identifier}\n"
			f"  Model Identifier: {self.model_identifier}\n"
			f"  Score: {self.score}\n"
			f"  {sub_criteria_scores_str}\n"
			f"  {issues_str}"
		)

class GradingOutput:
	"""
	Represents the grading output for a set of solutions.
	"""

	def __init__(self, solution_grades: List['SolutionGrade'], grader_identifier: str):
		self.solution_grades = solution_grades
		self.grader_identifier = grader_identifier
	
	@property
	def overall_score(self) -> float:
		"""Calculate and return the overall score as the average of all solution grades."""
		# Ensure the solution_grades list is not empty to avoid division by zero
		if not self.solution_grades:
			raise ValueError("The solution_grades list cannot be empty.")
	
		total_score = sum(grade.score for grade in self.solution_grades)
		average_score = total_score / len(self.solution_grades)
		return average_score
	
	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'GradingOutput':
		"""Create a GradingOutput instance from JSON data."""
		solution_grades_data = data.get('solution_grades', [])
		solution_grades = [SolutionGrade.from_json(grade_data) for grade_data in solution_grades_data]
		grader_identifier = data.get('grader_identifier', '')  # Assume empty string if not present
		return cls(solution_grades, grader_identifier)
	
	def to_json(self) -> Dict[str, Any]:
		"""Convert the GradingOutput instance to a JSON-serializable dictionary."""
		solution_grades_data = [solution_grade.to_json() for solution_grade in self.solution_grades]
		return {
			'overall_score': self.overall_score,
			'solution_grades': solution_grades_data,
			'grader_identifier': self.grader_identifier
		}
	
	def str_including_solutions(self):
		def add_tab(string):
			lines = string.split('\n')
			lines_with_tabs = ['\t' + line for line in lines]
			result = '\n'.join(lines_with_tabs)
			return result
			
		solution_grades_str = add_tab('\n  '.join(str(grade) for grade in self.solution_grades))
		return str(self) + "\nSolution grades:\n" + solution_grades_str

	
	def __str__(self) -> str:
		def add_tab(string):
			lines = string.split('\n')
			lines_with_tabs = ['\t' + line for line in lines]
			result = '\n'.join(lines_with_tabs)
			return result
			
		solution_grades_str = add_tab('\n  '.join(str(grade) for grade in self.solution_grades))
		return (
			f"GradingOutput ({self.grader_identifier}):\n"
			f"  Overall Score: {self.overall_score}\n"
			f"  Solutions Count: {len(self.solution_grades)}"
		)
			
class TestCase:
	def __init__(self, data: Dict[str, Any]):
		self.parameters = data.get('input', {})
		self.expected_output = data.get('expected_output', {})
	
	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'TestCase':
		return cls(data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			'input': self.parameters,
			'expected_output': self.expected_output
		}
	
	def __str__(self) -> str:
		inputs_str = ', '.join(f'{k} = {v}' for k, v in self.parameters.items())
		expected_output_str = ', '.join(f'{v}' for v in self.expected_output)
		return f'Input: {inputs_str}; Expected Output: {expected_output_str}'


class FunctionPrototype:
	def __init__(self, data):
		self.function_name = data["function_name"]
		self.parameters = [Parameter(p) for p in data["parameters"]]
		self.return_values = [ReturnValue(r) for r in data["return_values"]]

	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'FunctionPrototype':
		return cls(data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			"function_name": self.function_name,
			"parameters": [param.to_json() for param in self.parameters],
			"return_values": [rv.to_json() for rv in self.return_values]
		}

	def __str__(self):
		params_str = ", ".join([str(p) for p in self.parameters])
		return_values_str = ", ".join([str(r) for r in self.return_values])
		return f"{self.function_name}({params_str}) -> {return_values_str}"
		
	def genericize(self):
		generic_data = {
			"function_name": "function",
			"parameters": [{"name": chr(97 + i), "type": param.type} for i, param in enumerate(self.parameters)],
			"return_values": [{"type": rv.type} for rv in self.return_values]
		}
		return FunctionPrototype(generic_data)
	
	def get_python_type(self, param_type, input):
		# Based on the type, convert the string representation to the appropriate Python object
		param_type = re.search(r'^Optional\[(.*)\]$', param_type).group(1) if re.search(r'^Optional\[(.*)\]$', param_type) else param_type
		
		if param_type == "int":
			return int(input)
		elif param_type == "float":
			return float(input)
		elif param_type == "str":
			return ast.literal_eval(f'"{input}"')  # Adding double quotes around the string
		elif param_type == "bool":
			return input.lower() == "true"
		elif '[' in param_type and isinstance(input, str):  # Ensure input is a string
			# Using ast.literal_eval to safely evaluate the string representation
			return ast.literal_eval(input)
		else:
			return input  # Return the input as-is for unsupported types or if input is not a string
		
	def get_parameter_values(self, test_case: TestCase) -> Dict[str, Any]:
		converted_params = {}
		
		for param in self.parameters:
			converted_params[param.name] = self.get_python_type(param.type, test_case.parameters[param.name])
		return converted_params
		
	def get_ordered_parameter_values(self, test_case) -> List[str]:
		ordered_parameters = []
		
		parameter_values = self.get_parameter_values(test_case)
		
		for p in self.parameters:
			ordered_parameters.append(parameter_values[p.name])
		return ordered_parameters
		
	def get_return_values(self, test_case: TestCase) -> Dict[str, Any]:
		converted_retvals = []
		
		expectedOutput = test_case.expected_output
		
		for retval, expected in zip(self.return_values, expectedOutput):
			# Extract the type of the parameter
			converted_retvals.append(self.get_python_type(retval.type, expected))
			
		if len(converted_retvals) == 1:
			return converted_retvals[0]
		elif len(converted_retvals) > 1:
			return tuple(converted_retvals)

class Parameter:
	def __init__(self, data):
		self.name = data["name"]
		self.type = data["type"]

	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'Parameter':
		return cls(data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"type": self.type
		}

	def __str__(self):
		return f"{self.name}: {self.type}"

class ReturnValue:
	def __init__(self, data):
		self.type = data["type"]

	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'ReturnValue':
		return cls(data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			"type": self.type
		}

	def __str__(self):
		return self.type

class Prompt:
	def __init__(self, data: Dict[str, any]):
		self.prompt_id = data["prompt_id"]
		self.prompt = data["prompt"]
		self.genericize = data.get("genericize", None)
		self.sample_inputs_outputs = [TestCase(tc) for tc in data.get("sample_inputs_outputs", [])]
		self.input_code = data.get("input_code", None)
	
	def __str__(self):
		genericize_str = "Genericize" if self.genericize else "Do not genericize"
		sample_io_str = ', '.join(str(tc) for tc in self.sample_inputs_outputs)
		return f'Prompt ID: {self.prompt_id}, Prompt: "{self.prompt}", {genericize_str}, Sample Inputs/Outputs: [{sample_io_str}], Input Code: {self.input_code}'
	
	@classmethod
	def from_json(cls, data: Dict[str, any]) -> 'Prompt':
		return cls(data)
	
	def to_json(self) -> Dict[str, any]:
		return {
			"prompt_id": self.prompt_id,
			"prompt": self.prompt,
			"genericize": self.genericize,
			"sample_inputs_outputs": [tc.to_json() for tc in self.sample_inputs_outputs],
			"input_code": self.input_code
		}

class LLMProblemInput:
	def __init__(self, data: Dict[str, Any]):
		self.problem_id = data.get('problem_id', '')
		self.prompt_id = data.get('prompt_id', '')
		self.prompt = data.get('prompt', '')
		self.sample_inputs_outputs = [TestCase.from_json(tc) for tc in data.get('sample_inputs_outputs', [])]
		self.input_code = data.get('input_code', '')
		self.function_prototype = FunctionPrototype.from_json(data.get('function_prototype', {}))
	
	@classmethod
	def from_json(cls, json_data: Dict[str, Any]) -> 'LLMProblemInput':
		return cls(json_data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			'problem_id': self.problem_id,
			'prompt_id': self.prompt_id,
			'prompt': self.prompt,
			'sample_inputs_outputs': [tc.to_json() for tc in self.sample_inputs_outputs],
			'input_code': self.input_code,
			'function_prototype': self.function_prototype.to_json()
		}
	
	def __str__(self) -> str:
		return json.dumps(self.to_json(), indent=2)

class ProblemDefinition:
	def __init__(self,
				 identifier: str,
				 description: str,
				 prompts: List[Prompt],
				 function_prototype: FunctionPrototype,
				 correctness_test_suite: Optional[List[TestCase]] = None,
				 optimal_solution: Optional[str] = None,
				 additional_instructions: Optional[str] = None,
				 tags: Optional[List[str]] = None):
		self.identifier = identifier
		self.description = description
		self.prompts = prompts
		self.function_prototype = function_prototype
		self.correctness_test_suite = correctness_test_suite
		self.optimal_solution = optimal_solution
		self.additional_instructions = additional_instructions
		self.tags = tags
	
	@classmethod
	def from_json(cls, data: Dict[str, Any]) -> 'ProblemDefinition':
		function_prototype = FunctionPrototype.from_json(data.get('function_prototype', {}))
		prompts = [Prompt.from_json(prompt_data) for prompt_data in data.get("prompts", [])]
		correctness_test_suite = [TestCase.from_json(test_case) for test_case in data.get('correctness_test_suite', [])]
		return cls(
			identifier=data.get('identifier', ''),
			description=data.get('description', ''),
			prompts=prompts,
			function_prototype=function_prototype,
			correctness_test_suite=correctness_test_suite,
			optimal_solution=data.get('optimal_solution', None),
			additional_instructions=data.get('additional_instructions', None),
			tags=data.get('tags', None)
		)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			'identifier': self.identifier,
			'description': self.description,
			'prompts': [prompt.to_json() for prompt in self.prompts],
			'function_prototype': self.function_prototype.to_json(),
			'correctness_test_suite': [test_case.to_json() for test_case in self.correctness_test_suite],
			'optimal_solution': self.optimal_solution,
			'additional_instructions': self.additional_instructions,
			'tags': self.tags
		}
	
	def __str__(self) -> str:
		prompts_str = '\n    '.join(str(prompt) for prompt in self.prompts)
		correctness_test_suite_str = '\n    '.join(str(test_case) for test_case in self.correctness_test_suite) if self.correctness_test_suite else "No Test Cases"
		tags_str = ', '.join(self.tags) if self.tags else "No Tags"
		return (
			f"ProblemDefinition {self.identifier}:\n"
			f"  Description: {self.description}\n"
			f"  Prompts:\n    {prompts_str}\n"
			f"  Function Prototype: {self.function_prototype}\n"
			f"  Correctness Test Suite:\n    {correctness_test_suite_str}\n"
			f"  Optimal Solution: {self.optimal_solution or 'Not Provided'}\n"
			f"  Additional Instructions: {self.additional_instructions or 'Not Provided'}\n"
			f"  Tags: {tags_str}"
		)
	
	def get_llm_problem_inputs(self) -> list[LLMProblemInput]:
		llm_problem_inputs = []
		for prompt in self.prompts:
			llm_input_data = {
				'problem_id': self.identifier,
				'prompt_id': prompt.prompt_id,
				'prompt':  prompt.prompt,
				'sample_inputs_outputs': [tc.to_json() for tc in prompt.sample_inputs_outputs],
				'input_code': prompt.input_code,
				'function_prototype': self.function_prototype.to_json()
			}
			llm_problem_input = LLMProblemInput(llm_input_data)
			llm_problem_inputs.append(llm_problem_input)
		return llm_problem_inputs

class LLMProblemInput:
	def __init__(self, data: Dict[str, Any]):
		self.problem_id = data.get('problem_id', '')
		self.prompt_id = data.get('prompt_id', '')
		self.prompt = data.get('prompt', '')
		self.sample_inputs_outputs = [TestCase.from_json(tc) for tc in data.get('sample_inputs_outputs', [])]
		self.input_code = data.get('input_code', '')
		self.function_prototype = FunctionPrototype.from_json(data.get('function_prototype', {}))
	
	@classmethod
	def from_json(cls, json_data: Dict[str, Any]) -> 'LLMProblemInput':
		return cls(json_data)
	
	def to_json(self) -> Dict[str, Any]:
		return {
			'problem_id': self.problem_id,
			'prompt_id': self.prompt_id,
			'prompt': self.prompt,
			'sample_inputs_outputs': [tc.to_json() for tc in self.sample_inputs_outputs],
			'input_code': self.input_code,
			'function_prototype': self.function_prototype.to_json()
		}
	
	def __str__(self) -> str:
		return json.dumps(self.to_json(), indent=2)
	
