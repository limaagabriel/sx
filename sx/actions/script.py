import sys
import subprocess
from pathlib import Path
from sx.utils import get_package_root
from sx.stubs.settings import Settings


def run(args, unknown_args):
    settings = Settings(args.settings)
    scripts = settings.application.scripts

    if hasattr(scripts, args.name):
        working_dir = '.' 
        script_data = getattr(scripts, args.name)
        if script_data.context is not None: 
            working_dir = get_package_root(script_data.context)

        command = str((Path('scripts') / args.name /
                       script_data.entry).absolute())

        print('Executing script: %s' % command)
        if script_data.interpreter:
            interpreter = script_data.interpreter
            if script_data.interpreter == 'python':
                interpreter = str((Path(sys.prefix) / 'bin' / 'python').absolute())
            print('Using interpreter: %s' % interpreter)
            
            command = '%s %s' % (interpreter, command)

        print('Passing custom arguments: %s' % str(unknown_args))
        print('Working directory: %s' % working_dir)
        subprocess.Popen(
            command.split(' ') + unknown_args,
            cwd=working_dir,
            stdout=sys.stdout,
            stderr=sys.stdout
        )
    else:
        raise TypeError('script not found')
