import os
from sx.utils import get_package_root
from sx.stubs.settings import Settings


class Environment(object):
	def __init__(self, location, constants={}):
		self.__location = location
		self.__constants = constants
		self.__data = {}

	def __add(self, key, value, prefix):
		if prefix is not None:
			key = '{}{}'.format(prefix, key)
		self.__data[key] = value

	def add(self, key, value, prefix=None):
		if type(value) == Settings:
			if 'key' in value and value.key in self.__constants:
				self.__add(key, self.__constants[value.key], prefix)
			elif 'default' in value:
				self.__add(key, value.default, prefix)
		else:
			self.__add(key, value, prefix)

	def add_port(self, name, settings, prefix=None):
		port_key = '{}_PORT'.format(name.upper())
		port_value = getattr(settings.application.packages, name).port
		self.add(port_key, port_value, prefix)

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

