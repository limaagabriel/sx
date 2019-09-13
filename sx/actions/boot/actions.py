import re
import sys
import time
import libtmux
from coolname import generate_slug

from sx.utils import run
from sx.utils import sort
from sx.utils import install
from sx.utils import copy_protocols
from sx.utils import execute_command
from sx.utils import clean_build_location
from sx.stubs.environment import Environment


def build(settings, args):
	buildable_types = ['python']
	selected_packages = list(settings.package)

	if args.packages is not None:
		def filter_fn(x): return x[0] in args.packages
		selected_packages = list(filter(filter_fn, selected_packages))

	if len(selected_packages) == 0:
		print('You should select at least one valid package')
		sys.exit(0)

	for package_name, package_data in selected_packages:
		build_action = copy_protocols
		clean_build_location(package_name)
		if package_data.type in buildable_types:
			build_action = install

		with Environment(package_name) as environment:
			environment.add_port(package_name, settings)

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
							environment.add(key, value)

					if 'profile' in package_data \
						and profile_type in package_data.profile \
						and chosen_profile in getattr(package_data.profile, profile_type):

						values = getattr(package_data.profile, profile_type)
						for key, value in getattr(values, chosen_profile):
							environment.add(key, value)
			
			for dependency in package_data.dependencies:
				environment.add_port(dependency, settings)
				dependency_data = getattr(settings.package, dependency)
				if dependency_data.available is None or dependency_data.available:
					build_action(dependency, package_data.type, package_name)

			if package_data.variables is not None:
				for key, value in package_data.variables:
					environment.add(key, value)

			if package_data.available is None or package_data.available:
				build_action(package_name, package_data.type, package_name)
		if package_data.postBuild is not None:
			execute_command(package_name, 'postBuild', package_data)


def start(settings, args):
	processes = []
	selected_packages = list(settings.package)

	if args.packages is not None:
		def filter_fn(x): return x[0] in args.packages
		selected_packages = list(filter(filter_fn, selected_packages))

	if len(selected_packages) == 0:
		print('You should select at least one valid package')
		sys.exit(0)

	server = libtmux.Server()
	session_name = generate_slug(2)
	session = server.new_session(session_name)

	for package_name, package_settings in sort(selected_packages):
		run(session, package_name, package_settings)
	session.list_windows()[0].kill_window()

	try:
		print('Session name: {}'.format(session_name))
		print('Press Ctrl+C to stop')
		
		while True:
			time.sleep(86400)
	except KeyboardInterrupt:
		print('Requesting services to stop')

		for window in session.list_windows():
			while True:
				try:
					cmd = window.attached_pane.cmd('kill -SIGINT $PID')
					cmd.process.wait(timeout=1)
					break
				except Exception:
					pass

		try:
			for window in session.list_windows():
				window.kill_window()
		except libtmux.exc.LibTmuxException:
			print('Exited successfully!')

