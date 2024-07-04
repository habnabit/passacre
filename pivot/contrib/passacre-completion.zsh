#compdef passacre

_passacre_subcommand_schema () {
    

    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=('add:add a schema' 'remove:remove a schema' "set-name:change a schema's name" "set-value:change a schema's value")
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in
    

        (add)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':name: ' ':value: ' \
                && return 0
            ;;
        

        (remove)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':name:_passacre_schemata' \
                && return 0
            ;;
        

        (set-name)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':oldname:_passacre_schemata' ':newname: ' \
                && return 0
            ;;
        

        (set-value)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':name:_passacre_schemata' ':value: ' \
                && return 0
            ;;
        

    esac
}
    

_passacre_subcommand_site () {
    

    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=('add:add a site to a config file' "config:change a site's configuration" "hash:hash a site's name" 'hash-all:hash all non-hashed sites' 'remove:remove a site from a config file' "set-name:change a site's domain" "set-schema:change a site's schema")
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in
    

        (add)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site: ' ':schema:_passacre_schemata' '(-N)--new-schema=[a schema value for the new schema]:VALUE: ' '(--new-schema)-N=[a schema value for the new schema]:VALUE: ' \
                && return 0
            ;;
        

        (config)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site:_passacre_sites' '(-a)--hashed[hash the site name]' '(--hashed)-a[hash the site name]' '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' ':name: ' ':value: ' \
                && return 0
            ;;
        

        (hash)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site:_passacre_sites' '(-m)--method=[which hash method to use]: :_passacre_hash_methods' '(--method)-m=[which hash method to use]: :_passacre_hash_methods' "(-n)--no-newline[don't write a newline after the hash]" "(--no-newline)-n[don't write a newline after the hash]" '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' \
                && return 0
            ;;
        

        (hash-all)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '(-m)--method=[which hash method to use]: :_passacre_hash_methods' '(--method)-m=[which hash method to use]: :_passacre_hash_methods' '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' \
                && return 0
            ;;
        

        (remove)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site:_passacre_sites' \
                && return 0
            ;;
        

        (set-name)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':oldname:_passacre_sites' ':newname: ' \
                && return 0
            ;;
        

        (set-schema)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site:_passacre_sites' ':schema:_passacre_schemata' \
                && return 0
            ;;
        

    esac
}
    

_passacre_subcommand () {
    

    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=('config:view/change global configuration' "entropy:display each site's password entropy" 'generate:generate a password' 'info:information about the passacre environment' 'init:initialize an sqlite config' 'schema:actions on schemata' 'site:actions on sites')
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in
    

        (config)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '(-s)--site=[the site to operate on or omitted for global config]: :_passacre_sites' '(--site)-s=[the site to operate on or omitted for global config]: :_passacre_sites' '(-a)--hashed[hash the site name]' '(--hashed)-a[hash the site name]' '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' ':name: ' ':value: ' \
                && return 0
            ;;
        

        (entropy)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '--schema[show entropy by schema instead of by site]' \
                && return 0
            ;;
        

        (generate)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':site:_passacre_sites' '(-o)--override-config=[a JSON dictionary of config values to override]:CONFIG: ' '(--override-config)-o=[a JSON dictionary of config values to override]:CONFIG: ' '(-u)--username=[username for the site]: : ' '(--username)-u=[username for the site]: : ' "(-n)--no-newline[don't write a newline after the password]" "(--no-newline)-n[don't write a newline after the password]" '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' \
                && return 0
            ;;
        

        (info)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' \
                && return 0
            ;;
        

        (init)
            _arguments -S \
                 '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' ':path: ' '(-y)--from-yaml=[optional input YAML config file to convert from]:YAML:_files' '(--from-yaml)-y=[optional input YAML config file to convert from]:YAML:_files' \
                && return 0
            ;;
        

        (schema)
            _arguments -S \
                '*::site cmd:_passacre_subcommand_schema' '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' \
                && return 0
            ;;
        

        (site)
            _arguments -S \
                '*::site cmd:_passacre_subcommand_site' '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' '--by-schema[list sites organized by schema]' "--omit-hashed[don't list hashed sites]" '(-a)--hashed[hash the site name]' '(--hashed)-a[hash the site name]' '(-c)--confirm[confirm prompted password]' '(--confirm)-c[confirm prompted password]' \
                && return 0
            ;;
        

    esac
}
    

_passacre () {
    _arguments -S \
        '*::cmd:_passacre_subcommand' \
        '(-h)--help[show this help message and exit]' '(--help)-h[show this help message and exit]' "(-V)--version[show program's version number and exit]" "(--version)-V[show program's version number and exit]" '(-v)--verbose[increase output on errors]' '(--verbose)-v[increase output on errors]' '(-f)--config=[specify a config file to use]: : ' '(--config)-f=[specify a config file to use]: : ' \
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

