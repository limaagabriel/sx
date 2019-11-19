import importlib
from sx.stubs.settings import Settings


def run(args):
    settings = Settings(args.settings)
    module_name = 'sx.actions.export.{}'.format(args.format)
    module = importlib.import_module(module_name)
    action = getattr(module, 'export')
    action(settings, args)
