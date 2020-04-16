import os
import re
import sys
import time
import yaml
import signal

from sx.utils import sort
from sx.utils import install
from sx.utils import close_session
from sx.utils import create_session
from sx.utils import copy_protocols
from sx.utils import execute_command
from sx.utils import select_packages
from sx.utils import clean_build_location
from sx.stubs.environment import Environment


def to_plain(d, prefix = '', result={}):
	for k, v in d.items():
		if type(v) == type(dict()):
			to_plain(v, prefix + str(k) + '.', result)
		else:
			result[prefix + str(k)] = str(v)
	return result

def select_constants(args):
	constants = {}
	
	if args.configure is not None:
		root = os.path.join('manifests', 'configuration')
		name = '{}.yml'.format(args.configure)
		configure = os.path.join(root, name)

		if not os.path.exists(configure):
			raise Exception('Preset file not found.')
		
		with open(configure, 'r') as stream:
			confs = yaml.safe_load(stream)
			constants = { **to_plain(confs) }

	for key, value in args.define:
		constants[key] = value
	return constants


def build(settings, args):
	buildable_types = ['python']
	constants = select_constants(args)
	selected_packages = select_packages(settings, args.packages)

	for package_name, package_data in sort(selected_packages):
		build_action = copy_protocols
		clean_build_location(package_name)
		if package_data.type in buildable_types:
			build_action = install

		with Environment(package_name, constants) as environment:
			environment.add_port(package_name, settings, package_data.prefix)

			if package_data.dependencies is not None:
				for dependency in package_data.dependencies:
					environment.add_port(dependency, settings, package_data.prefix)
					dependency_data = getattr(settings.application.packages, dependency)
					if dependency_data.available is None or dependency_data.available and not args.env_only:
						build_action(dependency, package_data.type, package_name)

			for key, value in settings.application.metadata:
				app_key = 'APPLICATION_{}'.format(key.upper())
				environment.add(app_key, value, package_data.prefix)

			if settings.application.variables is not None:
				for key, value in settings.application.variables:
					environment.add(key, value, package_data.prefix)

			if package_data.variables is not None:
				for key, value in package_data.variables:
					environment.add(key, value, package_data.prefix)

			if settings.application.profiles is not None:
				for profile_type, global_data in settings.application.profiles:
					def filter_fn(choice):
						pattern_str = r'^{}:[\w\-\d]+$'.format(profile_type)
						pattern = re.compile(pattern_str)
						return re.search(pattern, choice)

					chosen_profile = global_data.default
					match_choices = list(filter(filter_fn, args.profiles))
					if len(match_choices) > 0:
						key = '{}:'.format(profile_type)
						chosen_profile = match_choices[-1].replace(key, '')

					if chosen_profile not in global_data.options:
						message = 'Profile {}:{} is not an option.'
						print(message.format(profile_type, chosen_profile))
						sys.exit(0)

					if 'variables' in global_data and chosen_profile in global_data.variables:
						for key, value in getattr(global_data.variables, chosen_profile):
							environment.add(key, value, package_data.prefix)

					if 'profile' in package_data \
						and profile_type in package_data.profile \
						and chosen_profile in getattr(package_data.profile, profile_type):

						values = getattr(package_data.profile, profile_type)
						for key, value in getattr(values, chosen_profile):
							environment.add(key, value, package_data.prefix)

			if package_data.available is None or package_data.available and not args.env_only:
				build_action(package_name, package_data.type, package_name)
		if package_data.postBuild is not None:
			if package_data.postBuild.commands is not None and not args.skip_post:
				env = {}
				if package_data.postBuild.variables is not None:
					env = package_data.postBuild.variables.dict()
				execute_command(package_name, 'postBuild', package_data, env)


def start(settings, args):
	print('Booting selected packages')
	selected_packages = select_packages(settings, args.packages)
	session, name = create_session(selected_packages, args.develop)

	print('Session name: {}'.format(name))
	print('Press Ctrl+C to stop')

	def exit_fn(signum, frame):
		print('Requesting services to stop')
		if close_session(session):
			print('Exited successfully!')
			sys.exit(0)
		sys.exit(1)

	signal.signal(signal.SIGINT, exit_fn)
	signal.signal(signal.SIGTERM, exit_fn)
		
	while True:
		time.sleep(86400)
	
