import time
from sx.utils import run
from sx.utils import install
from sx.utils import copy_protocols
from sx.utils import execute_command
from sx.utils import clean_build_location
from sx.stubs.environment import Environment


def build(settings, args):
	buildable_types = ['python']
	for package_name, package_data in settings.package:
		build_action = copy_protocols
		clean_build_location(package_name)
		if package_data.type in buildable_types:
			build_action = install

		with Environment(package_name) as environment:
			environment.add_port(package_name, settings)
			
			for dependency in package_data.dependencies:
				environment.add_port(dependency, settings)
				build_action(dependency, package_data.type, package_name)

			if package_data.environment is not None:
				for key, value in package_data.environment:
					environment.add(key, value)

			if package_data.available is None or package_data.available:
				build_action(package_name, package_data.type, package_name)
		if package_data.postBuild is not None:
			execute_command(package_name, 'PostBuild', package_data.postBuild)


def start(settings, args):
	processes = []
	selected_packages = list(settings.package)

	if args.packages is not None:
		def filter_fn(x): return x[0] in args.packages
		selected_packages = filter(filter_fn, selected_packages)

	for package_name, package_settings in selected_packages:
		processes.append(run(package_name, package_settings))

	try:
		print('Press Ctrl+C to stop')
		
		while True:
			time.sleep(86400)
	except KeyboardInterrupt:
		print('Requesting services to stop')
		for process in processes:
			process.release()
