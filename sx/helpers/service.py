import os
import sys
import grpc
import time
import signal
import importlib
from functools import wraps
from concurrent import futures


class ServiceManager(object):
	__connections = {}

	class __ServiceInstance(object):
		def __init__(self, name, port):
			self.__messages = importlib.import_module('protocols.{}_pb2'.format(name))
			self.__services = importlib.import_module('protocols.{}_pb2_grpc'.format(name))
			self.__channel = grpc.insecure_channel('localhost:{}'.format(port))
			self.__stub_class = getattr(self.__services, '{}Stub'.format(name.capitalize()))

			self.__stub = self.__stub_class(self.__channel)

		def release(self):
			self.__channel.close()

		def __getattr__(self, name):
			return getattr(self.__stub, name)

		@property
		def messages(self):
			return self.__messages

		@property
		def services(self):
			return self.__services

	@staticmethod
	def boot_server(name, service, max_workers=10, on_exit=None):
		port = os.environ.get('{}_PORT'.format(name.upper()))
		server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
		server.add_insecure_port('[::]:{}'.format(port))
		
			
		add_base = 'add_{}Servicer_to_server'
		service_controller = ServiceManager.__ServiceInstance(name, port)
		add_method = getattr(service_controller.services, add_base.format(name.capitalize()))

		add_method(service, server)
		server.start()

		def exit_handler(signum, frame):
			server.stop(0)
			if on_exit is not None:
				on_exit()
			os.kill(os.getpid(), signal.SIGKILL)

		signal.signal(signal.SIGINT, exit_handler)
		signal.signal(signal.SIGTERM, exit_handler)

		while True:
			time.sleep(86400)

	@staticmethod
	def get(name):
		if name not in ServiceManager.__connections:
			env_key = '{}_PORT'.format(name.upper())
			
			port = os.environ.get(env_key)
			ServiceManager.__connect(name, port)
		return ServiceManager.__connections[name]


	@staticmethod
	def __connect(name, port):
		instance = ServiceManager.__ServiceInstance(name, port)
		ServiceManager.__connections[name] = instance

	@staticmethod
	def release():
		for name in ServiceManager.__connections:
			instance = ServiceManager.__connections[name]
			instance.release()

	@staticmethod
	def inject(*names):
		def inject_decorator(fn):
			@wraps(fn)
			def wrapper(*args, **kwargs):
				services = { 
					name: ServiceManager.get(name)
					for name in names
				}

				return fn(*args, **kwargs, **services)
			return wrapper
		return inject_decorator
