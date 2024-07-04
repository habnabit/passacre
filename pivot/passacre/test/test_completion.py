# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre.compat import argparse
from passacre import completion


def test_escape():
    assert completion.escape('foo bar') == "'foo bar'"

def test_escape_with_single_quotes():
    assert completion.escape("spam'd eggs") == '"spam\'d eggs"'

def test_with_meta_characters():
    assert completion.escape("spam'd eggs \\ $ \" `") == '"spam\'d eggs \\\\ \\$ \\" \\`"'


@pytest.fixture
def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--ecks', help='x')
    parser.add_argument('-y', '--why', action='store_true', help='y')
    subparsers = parser.add_subparsers(dest='command')
    spam_subparser = subparsers.add_parser('spam', help='spam')
    spam_subparser.add_argument('--spam', help='spam')
    eggs_subparser = subparsers.add_parser('eggs', help='eggs')
    eggs_subparsers = eggs_subparser.add_subparsers(dest='eggs_command')
    eggs1_parser = eggs_subparsers.add_parser('eggs1', help='eggs1')
    eggs1_parser.add_argument('spam', help='spam')
    eggs1_parser.add_argument('eggs', help='eggs')
    eggs2_parser = eggs_subparsers.add_parser('eggs2', help='eggs2')
    eggs2_parser.add_argument('--file', help='file').completer = completion.FilesCompleter()
    eggs2_parser.add_argument('--schema', help='schema').completer = completion.SchemataCompleter()
    eggs2_parser.add_argument('--site', help='site').completer = completion.SitesCompleter()
    eggs2_parser.add_argument('--hash-method', help='hash-method').completer = completion.HashMethodsCompleter()
    return parser


def test_zsh_completion(parser, capsys):
    completion.zsh_completion_for(parser)
    out, err = capsys.readouterr()
    assert not err
    out = '\n'.join(line.rstrip() for line in out.splitlines())
    assert out == """#compdef passacre

_passacre_subcommand_eggs () {


    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=('eggs1:eggs1' 'eggs2:eggs2')
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in


        (eggs1)
            _arguments -S \\
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':spam: ' ':eggs: ' \\
                && return 0
            ;;


        (eggs2)
            _arguments -S \\
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '--file=[file]: :_files' '--schema=[schema]: :_passacre_schemata' '--site=[site]: :_passacre_sites' '--hash-method=[hash-method]: :_passacre_hash_methods' \\
                && return 0
            ;;


    esac
}


_passacre_subcommand () {


    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=('eggs:eggs' 'spam:spam')
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in


        (eggs)
            _arguments -S \\
                '*::site cmd:_passacre_subcommand_eggs' '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' \\
                && return 0
            ;;


        (spam)
            _arguments -S \\
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '--spam=[spam]: : ' \\
                && return 0
            ;;


    esac
}


_passacre () {
    _arguments -S \\
        '*::cmd:_passacre_subcommand' \\
        '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '(-x)--ecks=[x]: : ' '(--ecks)-x=[x]: : ' '(-y)--why[y]' '(--why)-y[y]' \\
        && return 0
}


_passacre_sites () {
    local -a _passacre_site_list
    _passacre_site_list=($(passacre site --omit-hashed | cut -d: -f1))
    _wanted _passacre_site_list expl 'passacre sites' compadd -a _passacre_site_list
}


_passacre_schemata () {
    local -a _passacre_schema_list
    _passacre_schema_list=($(passacre schema | cut -d: -f1))
    _wanted _passacre_schema_list expl 'passacre schemata' compadd -a _passacre_schema_list
}


_passacre_hash_methods () {
    local -a _passacre_hash_method_list
    _passacre_hash_method_list=(keccak skein)
    _wanted _passacre_hash_method_list expl 'passacre hash methods' compadd -a _passacre_hash_method_list
}


_passacre "$@"
"""

def test_fish_completion(parser, capsys):
    completion.fish_completion_for(parser)
    out, err = capsys.readouterr()
    assert not err
    out = '\n'.join(line.rstrip() for line in out.splitlines())
    assert out == """

function __fish_passacre_using_command
	set cmd (commandline -opc)
	set argvpos 1
	set argvcount (count $argv)
	for c in $cmd
		if [ $argvpos -le $argvcount ]
			set arg $argv[$argvpos]
		else
			set arg --
		end
		switch $c
		case '-*'
			continue
		case $arg
			set argvpos (math $argvpos + 1)
		case '*'
			return 1
		end
	end
	test $argvpos -gt $argvcount
	return $status
end

function __fish_passacre_sites
	passacre site --omit-hashed | cut -d: -f1
end

function __fish_passacre_schemata
	passacre schema | cut -d: -f1
end


complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs1 ' -s h -l help -d 'show this help message and exit'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs1 '   -a '()'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs1 '   -d 'spam'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs1 "*"'   -a '()'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs1 "*"'   -d 'eggs'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 ' -s h -l help -d 'show this help message and exit'
complete  -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l file
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l file -d 'file'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l schema -a '(__fish_passacre_schemata)'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l schema -d 'schema'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l site -a '(__fish_passacre_sites)'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l site -d 'site'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l hash-method -a 'keccak skein'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs eggs2 '  -l hash-method -d 'hash-method'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs ' -s h -l help -d 'show this help message and exit'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs' -a 'eggs1' -d 'eggs1'
complete -f -c passacre -n '__fish_passacre_using_command passacre eggs' -a 'eggs2' -d 'eggs2'
complete -f -c passacre -n '__fish_passacre_using_command passacre spam ' -s h -l help -d 'show this help message and exit'
complete -f -c passacre -n '__fish_passacre_using_command passacre spam '  -l spam -a '()'
complete -f -c passacre -n '__fish_passacre_using_command passacre spam '  -l spam -d 'spam'
complete -f -c passacre -n '__fish_passacre_using_command passacre ' -s h -l help -d 'show this help message and exit'
complete -f -c passacre -n '__fish_passacre_using_command passacre ' -s x -l ecks -a '()'
complete -f -c passacre -n '__fish_passacre_using_command passacre ' -s x -l ecks -d 'x'
complete -f -c passacre -n '__fish_passacre_using_command passacre ' -s y -l why -d 'y'
complete -f -c passacre -n '__fish_passacre_using_command passacre' -a 'eggs' -d 'eggs'
complete -f -c passacre -n '__fish_passacre_using_command passacre' -a 'spam' -d 'spam'\
"""
