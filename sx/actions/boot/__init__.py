from sx.stubs.settings import Settings
from sx.actions.boot import actions


def run(args):
	settings = Settings(args.settings)
	action = getattr(actions, args.boot_action)
	action(settings, args)
