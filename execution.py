import sys
import os
from base_types import FunctionPrototype
from typing import *
import traceback
import tempfile
import multiprocessing
import json
import resource
import tracemalloc

class FunctionExecutionResult:
	def __init__(self, result=None, cpu_time=None, peak_memory=None, error=None, traceback=None, function_code=None, parameters=None):
		self.result = result
		self.cpu_time = cpu_time
		self.peak_memory = peak_memory
		self.error = error
		self.traceback = traceback
		self.function_code = function_code
		self.parameters = parameters
	
	def __repr__(self):
		return f"<FunctionExecutionResult result={self.result} cpu_time={self.cpu_time} peak_memory={self.peak_memory} error={self.error}>"

def executor_script(function_code_file, parameters_file, config_file, result_file):
	try:
		# Load the function code
		with open(function_code_file, 'r') as file:
			function_code = file.read()
	
		# Load the parameters
		with open(parameters_file, 'r') as file:
			parameters = json.load(file)
	
		# Load the configuration
		with open(config_file, 'r') as file:
			config = json.load(file)
	
		# Set default configurations if not provided
		iterations = config.get('iterations', 1)
		collect_cpu_time = config.get('collect_cpu_time', False)
		collect_memory_usage = config.get('collect_memory_usage', False)
	
		# Add necessary imports
		function_code = f"from typing import *\n\n{function_code}"
	
		# Execute the function code to define the function(s)
		exec_globals = {}
		exec(function_code, exec_globals)
	
		# Get the name of the last defined function
		last_function_name = [name for name in exec_globals if callable(exec_globals[name])][-1]
		function = exec_globals[last_function_name]
	
		# Initialize metrics
		total_time = 0
		peak_memory = 0
	
		# Execute function for specified iterations and collect metrics
		for i in range(iterations):
			if collect_memory_usage:
				tracemalloc.start()
	
			start_time = (resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime) if collect_cpu_time else None
			result = function(*parameters)
			end_time = (resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime) if collect_cpu_time else None
	
			if collect_cpu_time:
				total_time += (end_time - start_time)
	
			if collect_memory_usage:
				_, max_mem = tracemalloc.get_traced_memory()
				peak_memory = max(peak_memory, max_mem)
				tracemalloc.stop()
	
		metrics = {}
		if collect_cpu_time:
			metrics['cpu_time'] = total_time
		if collect_memory_usage:
			metrics['peak_memory'] = peak_memory
	
		# Write the result and metrics to the result file
		output = {'result': result, 'metrics': metrics}
		with open(result_file, 'w') as file:
			json.dump(output, file)
	
	except Exception as e:
		# Write any exception to the result file as a dictionary
		with open(result_file, 'w') as file:
			json.dump({'result': None, 'error': str(e), 'traceback': traceback.format_exc()}, file)
	

def execute_function(function_code, parameters, iterations, collect_cpu_time, collect_memory_usage):
	try:
		# Create temporary files for function_code, parameters, config, and result
		function_code_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.py')
		parameters_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
		config_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
		result_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
		
		# Write function_code and parameters to temporary files
		function_code_file.write(function_code)
		function_code_file.close()  # Close the file to ensure it's written to disk
		
		json.dump(parameters, parameters_file)
		parameters_file.close()  # Close the file to ensure it's written to disk
	
		# Write configuration to temporary file
		config_data = {
			"iterations": iterations,
			"collect_cpu_time": collect_cpu_time,
			"collect_memory_usage": collect_memory_usage
		}
		json.dump(config_data, config_file)
		config_file.close()  # Close the file to ensure it's written to disk
		
		# Create a separate Python process to run the executor_script
		process = multiprocessing.Process(target=executor_script, args=(function_code_file.name, parameters_file.name, config_file.name, result_file.name))
		process.start()
		process.join()
		
		# Load the result from the result file
		with open(result_file.name, 'r') as file:
			result_data = json.load(file)
		
		# Clean up temporary files
		os.unlink(function_code_file.name)
		os.unlink(parameters_file.name)
		os.unlink(config_file.name)
		os.unlink(result_file.name)
		
		# Construct the result object
		metrics = result_data.get('metrics', {})
		return FunctionExecutionResult(
			result=result_data.get('result'),
			cpu_time=metrics.get('cpu_time'),
			peak_memory=metrics.get('peak_memory'),
			error=result_data.get('error'),
			traceback=result_data.get('traceback'),
			function_code=function_code,
			parameters=parameters
		)
		
	except Exception as e:
		return FunctionExecutionResult(
			error=str(e),
			function_code=function_code,
			parameters=parameters
		)