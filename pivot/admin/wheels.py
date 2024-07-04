import os
import subprocess
import sys
import tempfile


def main():
    distdir = tempfile.mkdtemp()
    for target in ['.', 'passacre-metapackage']:
        subprocess.check_call(
            [sys.executable, 'setup.py', 'sdist', '-d', distdir],
            cwd=target)
    dists = [os.path.join(distdir, d) for d in os.listdir(distdir)]
    subprocess.check_call(
        [sys.executable, '-mpip', 'wheel', '--no-deps', '-w', 'wheelhouse'] + dists)


main()
