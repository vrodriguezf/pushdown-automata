#!/usr/bin/python
import os
import sys
import pandas as pd
from tabulate import tabulate

start_input = "" # input word to be found or not found
found = 0 # stores found state
accepted_config = [] # here we will post end configuration that was accepted

# production rules ("read input", "pop stack", "push stack", "next state")
productions = {}

# all states or non-terminals (not really necessary)
states = []

# list of alphabet symbols or terminals (not really necessary)
symbols = []

# list of stack alphabet symbols (not really necessary)
stack_symbols = []

# start state
start_symbol = ""

# start stack symbol
stack_start = ""

# list of acceptable states
acceptable_states = []

# E - accept on empty stack or F - acceptable state (default is false)
accept_with = ""

# recursively generate all possibility tree and terminate on success
def generate(state, input, stack, config, visited=None):
	global productions
	global found

	if visited is None:
		visited = set()

	total = 0

	# check for other tree node success
	if found:
		return 0

	# check for repeated configuration to avoid infinite recursion
	config_tuple = (state, input, stack)
	if config_tuple in visited:
		return 0
	visited.add(config_tuple)

	# check if our node can terminate with success
	if is_found(state, input, stack):
		found = 1 # mark that word is accepted so other tree nodes know and terminate

		# add successful configuration
		accepted_config.extend(config)

		return 1

	# check if there are further moves (or we have to terminate)
	moves = get_moves(state, input, stack, config)
	if len(moves) == 0:
		return 0

	# for each move do a tree
	for i in moves:
		total = total + generate(i[0], i[1], i[2], config + [(i[0], i[1], i[2])], visited)  
  
	return total

# checks if symbol is terminal or non-terminal
def get_moves(state, input, stack, config):
	global productions

	moves = []

	for i in productions:
		if i != state:
			continue

		for j in productions[i]:
			current = j
			new = []

			new.append(current[3])

			# read symbol from input if we have one
			if len(current[0]) > 0:
				if len(input) > 0 and input[0] == current[0]:
					new.append(input[1:])
				else:
					continue
			else:            
				new.append(input)

			# read stack symbol
			if len(current[1]) > 0:
				if len(stack) > 0 and stack[0] == current[1]:
					new.append(current[2] + stack[1:])
				else:
					continue
			else:
				new.append(current[2] + stack)

			moves.append(new)

	return moves

# checks if word already was generated somewhere in past
def is_found(state, input, stack):
	global accept_with
	global acceptable_states

	# check if all symbols are read
	if len(input) > 0: 
		return 0

	# check if we accept with empty stack or end state
	if accept_with == "E":
		if len(stack) < 1:  # accept if stack is empty
			return 1
		return 0
	else:
		for i in acceptable_states:
			if i == state: # accept if we are in terminal state
				return 1
		return 0

# print list of current configuration
def print_config(config):
	for i in config:
		print(i)

def parse_file(filename):
	global productions
	global start_symbol
	global start_stack
	global acceptable_states
	global accept_with

	try:
		lines = [line.rstrip() for line in open(filename)]

	except:
		return 0

	# add start state
	start_symbol = lines[3]

	# add start stack symbol
	start_stack = lines[4]

	# list of acceptable states
	acceptable_states.extend(lines[5].split())

	# E - accept on empty stack or F - acceptable state (default is false)
	accept_with = lines[6] 

	# add rules
	for i in range(7, len(lines)):
		production = lines[i].split()
		if len(production) < 5:
			print(f"Error: Malformed rule on line {i+1} of '{filename}':")
			print(f"  {lines[i]}")
			print("  (Expected at least 5 space-separated fields.)")
			import sys
			sys.exit(1)

		configuration = [(production[1], production[2], production[4], production[3])]

		if production[0] not in productions.keys(): 
			productions[production[0]] = []

		configuration = [tuple(s if s != "e" else "" for s in tup) for tup in configuration]

		productions[production[0]].extend(configuration)

	print(productions)
	print(start_symbol)
	print(start_stack)
	print(acceptable_states)
	print(accept_with)

	return 1

# checks if symbol is terminal or non-terminal
def done():
	if found:
		print(f"Hurray! Input word \"{start_input}\" is part of grammar.") 
	else:
		print(f"Sorry! Input word \"{start_input}\" is not part of grammar.") 

def main(automata_file, positive_test_file, negative_test_file):
	global start_input
	global found
	global accepted_config

	if not parse_file(automata_file):
		print("File not found!")
		return

	print("Automata built.")

	# Process positive tests
	with open(positive_test_file, 'r') as pos_file:
		positive_tests = [line.strip() for line in pos_file]
	p_strings_for_show = {"String": [], "Is Accepted": []}
	for test in positive_tests:
		start_input = test
		found = 0
		accepted_config = []
		try:
			generate(start_symbol, start_input, start_stack, 
								[(start_symbol, start_input, start_stack)])
		except RecursionError:
			print(f"RecursionError for input '{start_input}'. Marking as rejected.")
			found = 0
		p_strings_for_show["String"].append(start_input)
		p_strings_for_show["Is Accepted"].append(bool(found))
	p_strings_df = pd.DataFrame(p_strings_for_show)
	print(f"\nPositive Tests:\n{tabulate(p_strings_df, headers='keys', tablefmt='fancy_grid')}")

	# Process negative tests
	with open(negative_test_file, 'r') as neg_file:
		negative_tests = [line.strip() for line in neg_file]
	n_strings_for_show = {"String": [], "Is Rejected": []}
	for test in negative_tests:
		start_input = test
		found = 0
		accepted_config = []
		try:
			generate(start_symbol, start_input, start_stack, [(start_symbol, start_input, start_stack)])
		except RecursionError:
			print(f"RecursionError for input '{start_input}'. Marking as rejected.")
			found = 0
		n_strings_for_show["String"].append(start_input)
		n_strings_for_show["Is Rejected"].append(not found)
	n_strings_df = pd.DataFrame(n_strings_for_show)
	print(f"\nNegative Tests:\n{tabulate(n_strings_df, headers='keys', tablefmt='fancy_grid')}")

if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("Usage: main.py <automata_file> <positive_test_file> <negative_test_file>")
	else:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
