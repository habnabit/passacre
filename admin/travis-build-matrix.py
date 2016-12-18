from __future__ import print_function


def echo(s, **kw):
    print(s.rstrip().format(**kw))


echo('''
matrix:
  include:
''')

for compiler in ['clang', 'gcc']:
    for python in ['2.6', '2.7', '3.3', '3.4', '3.5']:
        echo('''
    - python: {pydot}
      env: TOXENV=cmake-backend,py{pynodot} _COMPILER={compiler}
''', compiler=compiler, pydot=python, pynodot=python.replace('.', ''))

echo('''
    - python: 2.7
      env: TOXENV=kcov _COMPILER=clang _KCOV=1

    - python: 2.7
      env: TOXENV=rust-kcov _COMPILER=clang _KCOV=1
''')
