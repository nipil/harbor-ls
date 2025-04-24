# harbor-ls

Simple cli project/repo/artefact scanner using Harbor API

No dependency (stdlib only)

Python 3.9+

# Configuration

Set environment variables :

    export HARBOR_USER=XXX
    export HARBOR_PASSWORD=YYY
    export HARBOR_REGISTRY=ZZZ

Or use command line arguments `-u`, `-p` (unsafe) and `-r` to set them.

# Usage

Additional options available :

- `--level` for logging levels
- `--format` for display format (defaults to `text`, `json` available)

You can filter the projects/repos scanned by using additional arguments in the following syntax :

- `projectname` : this would scan all artefacts of all repos of specified project
- `projectname/reponame` : this would scan all artefacts of the specified project/repo
- more than one filter can be provided on the command line, in which case any filter matching is done

Example :

    python3 cli.py -u me -p secret -r registry.example.org -f json myproject yourproject/thisrepo

# Sample output

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
