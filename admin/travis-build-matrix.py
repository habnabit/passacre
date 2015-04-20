print '''
matrix:
  include:
'''

for compiler in ['clang', 'gcc']:
    for python in ['2.6', '2.7', '3.2', '3.3', '3.4']:
        print '''
    - python: {pydot}
      env: TOXENV=py{pynodot},coveralls _COMPILER={compiler}
'''.format(compiler=compiler, pydot=python, pynodot=python.replace('.', ''))

print '''
    - python: 2.7
      env: TOXENV=gcovr,cpp-coveralls _COMPILER=clang

    - python: 2.7
      env: TOXENV=null _COMPILER=clang
      addons:
        coverity_scan:
          project:
            name: "habnabit/passacre"
            description: "Build submitted via Travis CI"
          notification_email: "coverity@habnab.it"
          build_command: "python setup.py build_ext"
          branch_pattern: coverity-scan
'''
