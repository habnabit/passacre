def echo(s, **kw):
    print(s.rstrip().format(**kw))


echo('''
matrix:
  include:
''')

for compiler in ['clang', 'gcc']:
    for python in range(7, 13):
        echo(f'''
    - python: 3.{python}
      env: TOXENV=py3{python} _COMPILER={compiler}
''')

# echo('''
#     - python: 3.12
#       env: TOXENV=rust-kcov _COMPILER=clang _KCOV=1
# ''')
