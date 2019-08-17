import os
import shutil
import subprocess
from subprocess import PIPE
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

def run(name, settings):
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

def execute_command(package_name, command_name, command):
	working_dir = get_package_root(package_name)
	message = [command_name, package_name, command]
	print('Executing {} for package "{}": {}'.format(*message))
	subprocess.run(command.split(' '), stdout=PIPE, stderr=PIPE, cwd=working_dir)
