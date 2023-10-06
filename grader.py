from abc import ABC, abstractmethod
from base_types import *
import execution
import time

class Grader(ABC):
	"""
	Abstract base class for graders.
	"""
	@classmethod
	@property
	@abstractmethod
	def identifier(self) -> str:
		"""
		A human-readable identifier for the grader.
		"""
		pass
		
	@classmethod
	def resolve_graders(cls, grader_names: List[str]) -> List['Grader']:
		subclass_mapping = {subclass.identifier: subclass for subclass in cls.__subclasses__()}
		instances = []
		for grader_name in grader_names:
			subclass = subclass_mapping.get(grader_name, CorrectnessGrader)
			instances.append(subclass())
		return instances
	
	@classmethod
	def run_function(cls, code: str, function_prototype: FunctionPrototype, test_case: TestCase, iterations=1, collect_cpu_time=False, collect_memory_usage=False) -> str:
		"""
		Runs generated Python code against a given test case.
		"""
		parameters = function_prototype.get_ordered_parameter_values(test_case)
		return execution.execute_function(code, parameters, iterations, collect_cpu_time, collect_memory_usage)
		pass
		
	@classmethod
	def can_grade(cls, problems: List[ProblemDefinition]) -> bool:
		"""
		Check if the current grader is capable of running the problem set.
		This method should be overridden by a child class if said class has stricter requirements.
		"""
		for p in problems:
			if not (all(var is not None for var in (p.identifier, p.description, p.prompts, p.function_prototype)) and len(p.prompts) > 0):
				return False
		return True
	
	@abstractmethod
	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		"""
		Grades the provided solutions against the problem definitions.
		"""
		pass
		
	def __str__(self) -> str:
		return f"{self.__class__.__name__}()"
		
class CorrectnessGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "correctness"
		
	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			function_prototype = problem.function_prototype
			for solution in solutions:
				number_correct = 0
				total_tests = 0
				issues = []
				if solution.problem_identifier == problem.identifier:
					for test_case in problem.correctness_test_suite:
						execution_results = Grader.run_function(solution.solution_code, function_prototype, test_case)
						actual_result = execution_results.result
						expected_result = function_prototype.get_return_values(test_case)
						total_tests += 1
						if expected_result == actual_result:
							number_correct += 1
						else:
							issues.append(f"Test failed: {test_case} Result: {actual_result}")
							
					score = 0
					if total_tests > 0:
						score = number_correct / total_tests
					grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, score, None, issues)
					solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)

class PerformanceGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "performance"
		
	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			function_prototype = problem.function_prototype
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					total_solution_time = 0
					total_optimal_time = 0
					issues = []
					for test_case in problem.correctness_test_suite:
						iterations = 100000
						solution_results = Grader.run_function(solution.solution_code, function_prototype, test_case, iterations=iterations, collect_cpu_time=True)
						optimal_results = Grader.run_function(problem.optimal_solution, function_prototype, test_case, iterations=iterations, collect_cpu_time=True)
						if solution_results.cpu_time is None or optimal_results.cpu_time is None:
							continue

						total_solution_time += solution_results.cpu_time
						total_optimal_time += optimal_results.cpu_time
					
					if total_solution_time > 0:
						overall_grade = min(1, total_optimal_time / total_solution_time)
						
						grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, overall_grade, None, issues)
						solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)

class MemoryGrader(Grader):
	@classmethod
	@property
	def identifier(self):
		return "memory"
		
	def grade(self, problems: List[ProblemDefinition], solutions: List[LLMSolution]) -> GradingOutput:
		solutionGrades = []
		for problem in problems:
			function_prototype = problem.function_prototype
			for solution in solutions:
				if solution.problem_identifier == problem.identifier:
					total_solution_peak_memory = 0
					total_optimal_peak_memory = 0
					issues = []
					for test_case in problem.correctness_test_suite:
						iterations = 1000
						solution_results = Grader.run_function(solution.solution_code, function_prototype, test_case, iterations=iterations, collect_memory_usage=True)
						optimal_results = Grader.run_function(problem.optimal_solution, function_prototype, test_case, iterations=iterations, collect_memory_usage=True)
						if solution_results.peak_memory is None or optimal_results.peak_memory is None:
							continue
		
						total_solution_peak_memory += solution_results.peak_memory
						total_optimal_peak_memory += optimal_results.peak_memory
					
					if total_solution_peak_memory > 0:
						overall_grade = min(1, total_optimal_peak_memory / total_solution_peak_memory)
						
						grade = SolutionGrade(problem.identifier, solution.prompt_identifier, solution.model_identifier, overall_grade, None, issues)
						solutionGrades.append(grade)
		return GradingOutput(solutionGrades, self.identifier)
