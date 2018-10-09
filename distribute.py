import shutil
import os
from subprocess import getstatusoutput

import re, pkg_resources

package = __file__.split(os.path.sep)[-2]

# Update `setup.py` to require currently installed versions of all packages
with open('./setup.py') as setup_file:
    new_setup_file_contents = setup_file_contents = setup_file.read()
    for install_requires_str in re.findall(
        r'\binstall_requires\s*=\s*\[[^\]]*\]',
        setup_file_contents
    ):
        item_indentation = ''
        indentation = ''
        for line in install_requires_str.split('\n'):
            match = re.match(r'^[ ]+', line)
            if match:
                group = match.group()
                if group:
                    if item_indentation:
                        if len(group) > len(item_indentation):
                            item_indentation = group
                        elif len(group) < len(item_indentation):
                            indentation = group
                    else:
                        indentation = item_indentation = group
        name_space = {}
        exec(install_requires_str, name_space)
        install_requires = name_space['install_requires']
        lines = ['install_requires=[']
        for requirement in install_requires:
            parts = re.split(r'([<>=]+)', requirement)
            if len(parts) == 3:
                referenced_package, operator, version = parts
            else:
                referenced_package = parts[0]
                operator = '>='
                version = '0'
            try:
                version = pkg_resources.get_distribution(referenced_package).version
            except pkg_resources.DistributionNotFound:
                # If no installed referenced_package is found--look for a project directory with a setup file
                requirement_setup_path = '../%s/setup.py' % referenced_package
                try:
                    with open(requirement_setup_path) as requirement_setup_file:
                        requirement_setup_contents = requirement_setup_file.read()
                        for version_str in re.findall(
                            r'\bversion\s*=\s*[\'"][^\'"]+[\'"]',
                            requirement_setup_contents
                        ):
                            name_space = {}
                            exec(version_str, name_space)
                            version = name_space['version']
                            break
                except FileNotFoundError:
                    pass
            lines.append("%s'%s'," % (item_indentation, referenced_package + operator + version))
        lines.append(indentation + ']')
        new_setup_file_contents = setup_file_contents.replace(
            install_requires_str,
            '\n'.join(lines)
        )
if new_setup_file_contents != setup_file_contents:
    with open('./setup.py', 'w') as setup_file:
        setup_file.write(new_setup_file_contents)

status, output = getstatusoutput(
    'python3.7 setup.py sdist bdist_wheel upload -r kroger'
)

print(output)

if status == 0:
    # Update the referenced_package version
    with open('./setup.py') as setup_file:
        new_setup_file_contents = setup_file_contents = setup_file.read()
        for version_str in re.findall(
            r'\bversion\s*=\s*[\'"][^\'"]+[\'"]',
            setup_file_contents
        ):
            name_space = {}
            exec(version_str, name_space)
            version_list = list(name_space['version'].split('.'))
            version_list[-1] = str(int(version_list[-1]) + 1)
            new_version = '.'.join(version_list)
            new_setup_file_contents = setup_file_contents.replace(
                version_str,
                "version='%s'" % new_version
            )
    if new_setup_file_contents != setup_file_contents:
        with open('./setup.py', 'w') as setup_file:
            setup_file.write(new_setup_file_contents)

for p in (
    './dist', './build', './%s.egg-info' % package,
    './.tox', './.cache', './venv',
    './.pytest_cache'
):
    if os.path.exists(p):
        shutil.rmtree(p)
