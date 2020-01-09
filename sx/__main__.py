import sys
import getpass
import argparse
import importlib


parser = argparse.ArgumentParser()

action_parsers = parser.add_subparsers(dest='action')
boot_parser = action_parsers.add_parser('boot', help='Manage sx-based applications')
boot_parser.add_argument('-s', '--settings', default='application.yml')

create_parser = action_parsers.add_parser('create', help='Create a new sx-based application')
export_parser = action_parsers.add_parser('export', help='Exports this application configuration into a predefined format')
export_parser.add_argument('-s', '--settings', default='application.yml')

boot_action_parsers = boot_parser.add_subparsers(dest='boot_action')
build_command = boot_action_parsers.add_parser('build', help='Builds application packages')
build_command.add_argument('-p', '--packages', nargs='+', default=None,
							help='Selects which packages should boot build (default: all packages)')
build_command.add_argument('-f', '--profiles', nargs='+', default=[],
							help='Selects which profiles to  use (default: use default profiles)')
build_command.add_argument('-s', '--skip-post', action='store_true',
							help='Skips post build steps', default=False)
build_command.add_argument('-e', '--env-only', action='store_true',
							help='Compiles only .env files', default=False)
build_command.add_argument('-d', '--define', action='append', nargs=2, default=[],
							metavar=('key', 'value'), help='Sets a configuration constant manually.')
build_command.add_argument('-c', '--configure', default=None,
							help='Defines a preset configuration file to use.')


start_command = boot_action_parsers.add_parser('start', help='Run packages')
start_command.add_argument('-p', '--packages', nargs='+', default=None,
							help='Selects which packages should boot run (default: all packages)')
start_command.add_argument('-d', '--develop', default=False, action='store_true',
							help='Starts packages for development with a suitable command (when provided).')


export_parser.add_argument('format', default='systemd', choices=('systemd',),
							help='Exports an app configuration into a set of systemd units')
export_parser.add_argument('-u', '--user', default=getpass.getuser(),
							help='Determines which user should execute this application')

create_parser.add_argument('name', help='Determine application name')


def main():
	args = parser.parse_args()
	if args.action is None:
		parser.print_help()
		sys.exit()

	package = 'sx.actions.{}'
	action = importlib.import_module(package.format(args.action))
	action.run(args)
