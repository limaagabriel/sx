import re
import sys
import time

from sx.utils import sort
from sx.utils import install
from sx.utils import close_session
from sx.utils import create_session
from sx.utils import copy_protocols
from sx.utils import execute_command
from sx.utils import select_packages
from sx.utils import clean_build_location
from sx.stubs.environment import Environment


def build(settings, args):
	buildable_types = ['python']
	selected_packages = select_packages(settings, args.packages)

	for package_name, package_data in sort(selected_packages):
		build_action = copy_protocols
		clean_build_location(package_name)
		if package_data.type in buildable_types:
			build_action = install

		with Environment(package_name) as environment:
			environment.add_port(package_name, settings, package_data.variablesPrefix)

			if settings.profile is not None:
				for profile_type, global_data in settings.profile:
					def filter_fn(choice):
						pattern = re.compile('^{}:[\w\-\d]+$'.format(profile_type, 'g'))
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
							environment.add(key, value, package_data.variablesPrefix)

					if 'profile' in package_data \
						and profile_type in package_data.profile \
						and chosen_profile in getattr(package_data.profile, profile_type):

						values = getattr(package_data.profile, profile_type)
						for key, value in getattr(values, chosen_profile):
							environment.add(key, value, package_data.variablesPrefix)
			
			for dependency in package_data.dependencies:
				environment.add_port(dependency, settings, package_data.variablesPrefix)
				dependency_data = getattr(settings.package, dependency)
				if dependency_data.available is None or dependency_data.available:
					build_action(dependency, package_data.type, package_name)

			if package_data.variables is not None:
				for key, value in package_data.variables:
					environment.add(key, value, package_data.variablesPrefix)

			if package_data.available is None or package_data.available:
				build_action(package_name, package_data.type, package_name)
		if package_data.postBuild is not None:
			execute_command(package_name, 'postBuild', package_data)


def start(settings, args):
	processes = []

	print('Booting selected packages')
	selected_packages = select_packages(settings, args.packages)
	session, name = create_session(selected_packages, args.develop)

	try:
		print('Session name: {}'.format(name))
		print('Press Ctrl+C to stop')
		
		while True:
			time.sleep(86400)
	except KeyboardInterrupt:
		print('Requesting services to stop')
		
		if close_session(session):
			print('Exited successfully!')

