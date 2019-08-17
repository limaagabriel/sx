import signal
import threading
from queue import Queue, Empty

class NonBlockingStreamReader(object):
	class __UnexpectedEndOfStream(Exception): pass

	def __init__(self, stream):
		self.__s = stream
		self.__q = Queue()

		self._t = threading.Thread(target=self.__populate_queue)
		self._t.daemon = True
		self._t.start() #start collecting lines from the stream

	def __populate_queue(self):
		while True:
			line = self.__s.readline()
			
			if line:
				self.__q.put(line)

	def readline(self, timeout=None):
		try:
			block = timeout is not None
			return self.__q.get(block=block, timeout=timeout)
		except Empty:
			return None


class ProcessLog(object):
	def __init__(self, name, process, name_body):
		self.__name = name
		self.__running = True
		self.__process = process
		self.__name_body = name_body

		self.__t1 = threading.Thread(target=self.__update, args=('stdout',))
		self.__t2 = threading.Thread(target=self.__update, args=('stderr',))

		self.__t1.start()
		self.__t2.start()

	def __update(self, stream_name):
		log_name = '{}_{}.log'.format(self.__name, stream_name)
		file_name = self.__name_body.format(log_name)
		stream = getattr(self.__process, stream_name)

		with open(file_name, 'w+') as file:
			while self.__running:
				for output in stream:
					if output is not None:
						file.write(output.decode('utf-8'))
						file.flush()

	def release(self):
		self.__running = False
		self.__t1.join()
		self.__t2.join()
		self.__process.send_signal(signal.SIGTERM)

