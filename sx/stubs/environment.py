import os
from sx.utils import get_package_root


class Environment(object):
	def __init__(self, location):
		self.__location = location
		self.__data = {}

	def add(self, key, value, prefix=None):
		if prefix is not None:
			key = '{}{}'.format(prefix, key)
		self.__data[key] = value

	def add_port(self, name, settings, prefix=None):
		port_key = '{}_PORT'.format(name.upper())
		port_value = getattr(settings.package, name).port

		if prefix is not None:
			port_key = '{}{}'.format(prefix, port_key)

		self.add(port_key, port_value)

	def __enter__(self):
		self.__data = {}
		return self

	def __exit__(self, *context):
		root = get_package_root(self.__location)
		environment_path = os.path.join(root, '.env')
		with open(environment_path, 'w+') as f:
			for key in self.__data:
				f.write('{}={}'.format(key, self.__data[key]))
				f.write('\n')

