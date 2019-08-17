import os
import sys


def run(args):
	if os.path.exists(args.name):
		message = 'ERROR: A directory named "{}" already exists'
		print(message.format(args.name))
		sys.exit()
	
	os.mkdir(args.name)
	os.mkdir(os.path.join(args.name, 'packages'))
	os.mkdir(os.path.join(args.name, 'protocols'))
	open(os.path.join(args.name, 'application.toml'), 'w').close()
