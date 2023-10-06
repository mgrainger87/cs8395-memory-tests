import serialization
import re
from base_types import LLMProblemInput, LLMSolution
import grader

def load_problems(base_path):
    return serialization.get_problems(base_path)

def construct_textual_prompt(llm_problem_input: LLMProblemInput) -> str:
    # Start with the textual prompt
    prompt_text = llm_problem_input.prompt
    
    # Add function prototype if available
    function_prototype = llm_problem_input.function_prototype
    if function_prototype:
        prompt_text += f"\n\nFunction Signature:\n{str(function_prototype)}"
    
    # Add sample inputs and outputs if available
    sample_io = llm_problem_input.sample_inputs_outputs
    if sample_io:
        sample_io_text = '\n\nSample Inputs and Outputs:\n'
        for i, test_case in enumerate(sample_io, start=1):
            sample_io_text += f"\nTest Case {i}:\n{str(test_case)}"
        prompt_text += sample_io_text
    
    # Add input code if available
    input_code = llm_problem_input.input_code
    if input_code:
        prompt_text += f"\n\nInput Code:\n{input_code}"
    
    prompt_text += "\n\nProvide a solution in Python. After analyzing the problem, provide your solution in a Markdown code block. Do not include tests in the Markdown code block. If there are multiple Markdown code blocks in your response, the last one will taken as your solution."

    return prompt_text

def generate_solutions(base_path, problem_definitions, model_identifier, llm):
    solutions = []	
    for problem_definition in problem_definitions:
        inputs = problem_definition.get_llm_problem_inputs()
        for problem_input in inputs:
            prompt_text = construct_textual_prompt(problem_input)            
            print(f"***Prompt:\n{prompt_text}")

            # prompt = PromptTemplate.from_template(prompt_text)
            # code_prompt = prompt.format()
            response = llm.predict(prompt_text)
            
            print(f"***Response:\n{response}")
            solution = extract_code(response)
            
            print(f"***Extracted solution:\n{solution}")
            solution = LLMSolution(problem_input.problem_id, model_identifier, problem_input.prompt_id, solution)
            solutions.append(solution)
            serialization.save_solution(base_path, solution)
    return solutions

def extract_code(response: str) -> str:
    # Try to find the last Python code block
    python_blocks = re.findall(r'``` ?python\n(.*?)\n```', response, re.DOTALL)
    if python_blocks:
        return python_blocks[-1].strip()
    
    # If no Python code block is found, try to find the last generic code block
    generic_blocks = re.findall(r'``` ?\n(.*?)\n```', response, re.DOTALL)
    if generic_blocks:
        return generic_blocks[-1].strip()
    
    return response

def load_problems_definitions(base_path):
    return load_problems(base_path)

def grade_solutions(base_path, problem_definitions, model_identifier, grader_identifier):
    grader_obj = grader.Grader.resolve_graders([grader_identifier])[0]
    if not grader_obj.can_grade(problem_definitions):
        return []
    print(f'Grading solutions for {base_path} from model {model_identifier} with grader {grader_identifier}')
    solutions = serialization.get_solutions(base_path, model_identifier)
    return grader_obj.grade(problem_definitions, solutions)
