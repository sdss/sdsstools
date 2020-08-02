# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date: 2017-09-27
# @Filename: tasks.py
# @License: BSD 3-Clause
# @Copyright: Brian Cherinka

import os
import shutil

from invoke import Collection, task


# This file contains tasks that can be easily run from the shell terminal using the Invoke
# python package. If you do not have invoke, install it with pip install
# To list the tasks available, type invoke --list from the top-level repo directory

@task
def clean_docs(ctx, target=None):
    """Cleans up the docs."""

    if target is None:
        target = ctx.sphinx.target

    print('Cleaning the docs')
    ctx.run(f'rm -rf {target}/_build')


@task
def build_docs(ctx, target=None, clean=False):
    """Builds the Sphinx docs"""

    if target is None:
        target = ctx.sphinx.target

    if clean:
        print('Cleaning the docs')
        ctx.run(f'rm -rf {target}/_build', pty=True)

    print('Building the docs')
    os.chdir(f'{target}')
    ctx.run('make html', pty=True)


@task
def show_docs(ctx, target=None):
    """Shows the Sphinx docs"""

    if target is None:
        target = ctx.sphinx.target

    print('Showing the docs')
    os.chdir(f'{target}/_build/html')
    ctx.run('open ./index.html')


@task
def clean(ctx):
    """Cleans up build files and test files."""

    print('Cleaning')
    ctx.run('rm -rf htmlcov **/htmlcov .coverage* **/.coverage*')
    ctx.run('rm -rf build')
    ctx.run('rm -rf dist')
    ctx.run('rm -rf **/*.egg-info *.egg-info')


@task(clean)
def deploy(ctx, test=False):
    """Deploy the project to PyPI"""

    assert shutil.which('twine') is not None, 'twine is not installed'
    assert shutil.which('wheel') is not None, 'wheel is not installed'

    if test is False:
        print('Deploying to PyPI!')
        repository_url = ''
    else:
        print('Deploying to Test PyPI!')
        repository_url = '--repository-url https://test.pypi.org/legacy/'

    ctx.run('python setup.py sdist bdist_wheel')
    ctx.run(f'twine upload {repository_url} dist/*')


@task(name='install-deps')
def install_deps(ctx, extras=None):
    """Install only dependencies from setup.cfg."""

    import setuptools

    if not os.path.exists('setup.cfg'):
        raise RuntimeError('setup.cfg cannot be found. If your project uses '
                           'requirement files use pip install -r instead.')

    if extras:
        extras = extras.split(',')
    else:
        extras = []

    config = setuptools.config.read_configuration('setup.cfg')

    if not config['options']:
        return

    options = config['options']

    setup_requires = options.get('setup_requires', [])
    install_requires = options.get('install_requires', [])

    requires = setup_requires + install_requires
    requires_str = (' '.join('"' + item + '"' for item in requires))
    if len(requires) > 0:
        ctx.run(f'pip install --upgrade {requires_str}', pty=True)

    for extra in extras:
        print(f'Installing extras={extra}')
        if 'extras_require' not in options:
            raise RuntimeError('extras_require is not defined')
        extra_deps = options['extras_require'].get(extra, [])
        if len(extra_deps) > 0:
            extra_deps_str = (' '.join('"' + item + '"' for item in extra_deps))
            ctx.run(f'pip install --upgrade {extra_deps_str}', pty=True)


# create a collection of tasks
ns = Collection(clean, deploy, install_deps)

# create a sub-collection for the doc tasks
docs = Collection('docs')
docs.add_task(build_docs, 'build')
docs.add_task(clean_docs, 'clean')
docs.add_task(show_docs, 'show')
ns.add_collection(docs)

ns.configure({'sphinx': {'target': 'docs/sphinx'}})
