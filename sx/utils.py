import os
import re
import sys
import time
import shutil
import libtmux
import subprocess

from subprocess import PIPE
from functools import reduce
from coolname import generate_slug
from sx.stubs.process_log import ProcessLog


def get_package_root(name):
	return os.path.join('packages', name)


def get_protocol_path(name):
	return os.path.join('protocols', name)


def get_package_protocols_path(name):
	return os.path.join(get_package_root(name), 'protocols')


def get_log_dir():
	return 'log'


def install(name, build_type, target):
	print('Compiling "{}" protocol for package "{}"'.format(name, target))
	target_path = get_package_root(target)
	protocol_path = get_protocol_path(name)
	
	command_body = 'python -m grpc.tools.protoc -I . ' + \
		'--{0}_out={1} --grpc_{0}_out={1} {2}.proto'

	command = command_body.format(build_type, target_path, protocol_path)
	subprocess.run(command.strip().split(' '))


def copy_protocols(name, build_type, target):
	print('Copying "{}" protocol for package "{}"'.format(name, target))
	root = get_package_protocols_path(target)
	if not os.path.exists(root):
		os.mkdir(root)

	protocol_name = '{}.proto'.format(name)
	protocol_target = os.path.join(root, protocol_name)
	protocol_source = '{}.proto'.format(get_protocol_path(name))
	shutil.copyfile(protocol_source, protocol_target)


def clean_build_location(target):
	protocol_path = os.path.join('packages', target, 'protocols')
	env_path = os.path.join('packages', target, '.env')
	
	subprocess.run(['rm', '-rf', protocol_path])
	subprocess.run(['rm', '-rf', env_path])

def ensure_log_dir_exists():
	if not os.path.exists(get_log_dir()):
		os.mkdir(get_log_dir())

def compile_command(command, data):
	result = '{}'.format(command)
	occurrences = re.finditer('\#\{\w+(\.\w+)*\}', command)
	tokens = set(map(lambda x: x.group(0), occurrences))

	for token in tokens:
		def reducer(a, b): return getattr(a, b)
		value = reduce(reducer, token[2:-1].split('.'), data)
		result = command.replace(token, str(value))
	return result

def run(session, name, settings, for_development):
	default_command = settings.start
	if for_development and settings.develop is not None:
		default_command = settings.develop

	window = session.new_window(name)
	command = compile_command(default_command, settings) 
	activate_path = os.path.join(sys.prefix, 'bin', 'activate')
	working_dir = os.path.join(os.getcwd(), get_package_root(name))

	commands = [
		'cd {}'.format(working_dir),
		'{} &'.format(command),
		'PID=$!'
	]
	
	if os.path.exists(activate_path):
		commands.insert(0, 'source {}'.format(activate_path))

	for cmd in commands:
		window.attached_pane.send_keys(cmd)

def run_process(name, settings):
	ensure_log_dir_exists()
	command = settings.start.split(' ')

	working_dir = get_package_root(name)
	log_body = os.path.join(get_log_dir(), '{}')
	process = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, cwd=working_dir)
	print('Running package {}@{}'.format(name, process.pid))
	
	if 'niceness' in settings:
		args = [settings.niceness, process.pid]
		command = 'renice -n {} -p {}'.format(*args)
		subprocess.run(command.split(' '))
		print('Adjusting niceness of {} to {}'.format(name, settings.niceness))

	return ProcessLog(name, process, log_body)

def execute_command(package_name, command_name, data):
	commands = getattr(data, command_name)
	if type(commands) == str:
		commands = [ commands ]

	for idx, command in enumerate(commands):
		command = compile_command(command, data)
		working_dir = get_package_root(package_name)
		message = [command_name, idx, package_name, command]
		print('Executing {} ({}) for package "{}": {}'.format(*message))
		subprocess.run(command.split(' '), stdout=PIPE, stderr=PIPE, cwd=working_dir)


def sort(packages):
	# Source: https://stackoverflow.com/a/11564323
	def topological_sort(source):
		"""perform topo sort on elements.

		:arg source: list of ``(name, [list of dependancies])`` pairs
		:returns: list of names, with dependancies listed first
		"""
		pending = [(name, set(deps)) for name, deps in source] # copy deps so we can modify set in-place       
		emitted = []        
		while pending:
			next_pending = []
			next_emitted = []
			for entry in pending:
				name, deps = entry
				deps.difference_update(emitted) # remove deps we emitted last pass
				if deps: # still has deps? recheck during next pass
					next_pending.append(entry) 
				else: # no more deps? time to emit
					yield name 
					emitted.append(name) # <-- not required, but helps preserve original ordering
					next_emitted.append(name) # remember what we emitted for difference_update() in next pass
			if not next_emitted: # all entries have unmet deps, one of two things is wrong...
				message = 'cyclic or missing dependency detected: {}'.format(next_pending)
				raise ValueError(message)
			pending = next_pending
			emitted = next_emitted

	names = list(map(lambda x: x[0], packages))
	input_list = list(map(lambda x: (x[0], x[1].dependencies), packages))
	correct_order = list(topological_sort(input_list))
	indexes = list(map(lambda x: names.index(x), correct_order))
	return list(map(lambda x: packages[x], indexes))


def create_session(packages, for_development):
	server = libtmux.Server()
	session_name = generate_slug(2)
	session = server.new_session(session_name)

	for package_name, package_settings in sort(packages):
		run(session, package_name, package_settings, for_development)
	session.list_windows()[0].kill_window()
	return session, session_name

def close_session(session):
	for window in session.list_windows():
		for _ in range(2):
			window.attached_pane.send_keys('kill -SIGINT $PID')

	try:
		for window in session.list_windows():
			window.kill_window()
			pass
	except libtmux.exc.LibTmuxException:
		return True
	return False

def select_packages(settings, choices):
	selected_packages = list(settings.package)

	if choices is not None:
		def filter_fn(x): return x[0] in choices
		selected_packages = list(filter(filter_fn, selected_packages))

	if len(selected_packages) == 0:
		print('You should select at least one valid package')
		sys.exit(0)

	return selected_packages
