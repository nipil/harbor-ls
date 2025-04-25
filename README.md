# harbor-ls

Simple cli project/repo/artefact scanner using Harbor API

No dependency (stdlib only)

Python 3.9+

# Python usage

    from harbor_ls import HarborLs
    scanner = HarborLs('reg.example.org', 'me', 'secret', ['myproject', 'yourproject/thisrepo'])
    result_dict = scanner.ls()

# CLI configuration

Set environment variables (in an environment file sourced by your shell, or through `export` shell statements) :

    HARBOR_USER=me
    HARBOR_PASSWORD=secret
    HARBOR_REGISTRY=registry.example.org

# Docker usage

An image is available at the following tag

    docker.io/nipil/harbor_ls

You can run it with something allong the following

    docker run --rm --env-file harbor_ls.env \
        -i -t docker.io/nipil/harbor_ls \
        -l info -f json myproject yourproject/thisrepo

# Public Harbor demo server

You can create a throwaway account on https://demo.goharbor.io to try this package out.

# CLI usage

Apart from environment variables, which you can set using `-u`,`-p` (unsafe) and`-r`, other options are available :

- `--level` for logging levels
- `--format` for display format (defaults to `text`, `json` available)

You can filter the projects/repos scanned by using additional arguments in the following syntax :

- `projectname` : this would scan all artefacts of all repos of specified project
- `projectname/reponame` : this would scan all artefacts of the specified project/repo
- more than one filter can be provided on the command line, in which case any filter matching is done

Example (with command line options instead of environment variables) :

    python3 -m harbor_ls -u me -p secret -r registry.example.org -f json myproject yourproject/thisrepo

# CLI sample output

Text ouput (with logging on stderr) :

    WARNING Not authorized for repo MYREPO1 : HTTP Error 403: Forbidden
    WARNING Not authorized for repo MYREPO2 : HTTP Error 403: Forbidden
    MYPROJECT1
        MYREPO1
        MYREPO2
    foo
        plugin-foo1
            2025-03-06T16:44:12.139Z sha256:xxx...xxx 1.3.0 latest
            2024-11-12T12:40:22.089Z sha256:yyy...yyy 1
        plugin-foo2
            2025-03-06T16:47:05.948Z sha256:zzz...zzz 1.3.0 latest
            2024-11-12T12:39:52.070Z sha256:ttt...ttt
    docker
        foo
        bar
        baz

JSON output (with logging on stderr)

    WARNING Not authorized for repo MYREPO1 : HTTP Error 403: Forbidden
    WARNING Not authorized for repo MYREPO2 : HTTP Error 403: Forbidden
    {
        "MYPROJECT1": {
            "MYREPO1": [],
            "MYREPO2": []
        },
        "foo": {
            "plugin-foo1": [
                {
                    "time": "2025-03-06T16:44:12.139Z",
                    "digest": "sha256:xxx...xxx",
                    "tags": [
                        "latest",
                        "1.3.0"
                    ]
                },
                {
                    "time": "2024-11-12T12:40:22.089Z",
                    "digest": "sha256:yyy...yyy",
                    "tags": [
                        "1"
                    ]
                }
            ],
            "plugin-foo2": [
                {
                    "time": "2025-03-06T16:47:05.948Z",
                    "digest": "sha256:zzz...zzz",
                    "tags": [
                        "latest",
                        "1.3.0"
                    ]
                },
                {
                    "time": "2024-11-12T12:39:52.070Z",
                    "digest": "sha256:ttt...ttt",
                    "tags": []
                }
            ]
        },
        "docker": {
            "foo": [],
            "bar": [],
            "baz": []
        }
    }
