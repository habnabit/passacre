print '''
matrix:
  include:
'''

for compiler in ['clang', 'gcc']:
    for python in ['2.6', '2.7', '3.3', '3.4', '3.5']:
        print '''
    - python: {pydot}
      env: TOXENV=py{pynodot},coveralls _COMPILER={compiler}
'''.format(compiler=compiler, pydot=python, pynodot=python.replace('.', ''))
