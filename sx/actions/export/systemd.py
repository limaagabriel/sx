import os
import shutil
from sx.utils import sort
from sx.utils import compile_command
from sx.utils import get_package_root


def get_command(data):
    tokens = data.start.split()
    command = ' '.join([shutil.which(tokens[0]), *tokens[1:]])

    return compile_command(command, data)


def export_target(name, services, path):
    with open(os.path.join(path, name), 'w') as stream:
        stream.write('[Unit]\n')
        stream.write('After=network.target\n')
        stream.write('Wants={}\n\n'.format(' '.join(services)))
        
        stream.write('[Install]\n')
        stream.write('WantedBy=multi-user.target\n')


def export_service(name, service_name, target, user, data, dependencies, path):
    with open(os.path.join(path, service_name), 'w') as stream:
        stream.write('[Unit]\n')
        if len(dependencies) == 0:
            stream.write('After=network.target\n')
        else:
            stream.write('After={}\n'.format(' '.join(dependencies)))
        stream.write('PartOf={}\n'.format(target))
        stream.write('Description={}\n\n'.format(data.description))

        stream.write('[Service]\n')
        if 'niceness' in data:
            stream.write('Nice={}\n'.format(data.niceness))
        if 'restart' in data:
            stream.write('Restart={}\n'.format(data.restart))
            stream.write('RestartSec=10\n')
        stream.write('ExecStartPre=/bin/sleep 2\n')
        stream.write('Environment="RUNTIME=systemd"\n')
        stream.write('Environment="RUNTIME_ID={}"\n'.format(target))
        stream.write('ExecStart={}\n'.format(get_command(data)))
        stream.write('WorkingDirectory={}\n\n'.format(os.path.abspath(get_package_root(name))))
        
        stream.write('[Install]\n')
        stream.write('WantedBy={}\n'.format(target))


def export(settings, args):
    service_names = []
    path = os.path.join('manifests', 'systemd')
    target_name = settings.application.metadata.name.lower().replace(' ', '-')


    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
    
    os.makedirs(path)
    for name, package_data in settings.application.packages:
        service_name = target_name + '-' + name + '.service'
        dependencies = [
            target_name + '-' + dependency + '.service'
            for dependency in package_data.dependencies
        ]

        service_names.append(service_name)

        export_service(name, service_name, target_name + '.target', args.user, package_data, dependencies, path)
    export_target(target_name + '.target', service_names, path)

