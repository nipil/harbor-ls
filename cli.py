#!/usr/bin/env python3

import sys

if sys.version_info.major == 3 and sys.version_info.minor < 9:
    print("Python 3.9 or higher is required.", file=sys.stderr)
    sys.exit(1)

import json
import logging
import os
import sys
import urllib.error
import urllib.request
from argparse import ArgumentParser
from base64 import b64encode


class App:

    def __init__(self, user: str, password: str, registry: str, fmt: str, filters: list[str]) -> None:
        self.user = user
        self.password = password
        self.registry = registry
        self.format = fmt
        self.filters = [_filter.split('/') for _filter in filters]
        self.basic_token = b64encode(f'{self.user}:{self.password}'.encode()).decode()

    def matches_filter(self, names: list[str]) -> bool:
        if len(self.filters) == 0:
            return True
        for _filter in self.filters:
            for a, b in zip(names, _filter):
                if a != b:
                    break
            else:
                return True
        else:
            return False

    def api_auth_get(self, url: str):
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Basic {self.basic_token}')
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)

    def api_get_projects(self) -> list[dict]:
        url = f'https://{self.registry}/api/v2.0/projects'
        return self.api_auth_get(url)

    def get_projects(self) -> list[str]:
        return [item['name'] for item in self.api_get_projects()]

    def api_get_project_repos(self, project: str) -> list[dict]:
        url = f'https://{self.registry}/api/v2.0/projects/{project}/repositories'
        return self.api_auth_get(url)

    def get_project_repos(self, project: str) -> list[str]:
        return [item['name'].split('/')[1] for item in self.api_get_project_repos(project)]

    def api_get_project_repo_artefacts(self, project: str, repo: str) -> list[dict]:
        url = f'https://{self.registry}/api/v2.0/projects/{project}/repositories/{repo}/artifacts'
        return self.api_auth_get(url)

    def get_project_repo_artefacts(self, project: str, repo: str) -> list[dict]:
        return [{'time': artefact['push_time'], 'digest': artefact['digest'],
                 'tags': [] if artefact['tags'] is None else [tag['name'] for tag in artefact['tags']]} for artefact in
                self.api_get_project_repo_artefacts(project, repo)]

    def scan_project_repo(self, project: str, repo: str) -> list[dict]:
        logging.info(f'Scanning {self.registry} / {project} / {repo}')
        try:
            artefacts = self.get_project_repo_artefacts(project, repo)
        except urllib.error.HTTPError as e:
            logging.warning(f'Not authorized for repo {repo} : {e}')
            return []
        return artefacts

    def scan_project(self, project: str) -> dict:
        logging.info(f'Scanning {self.registry} / {project}')
        try:
            repos = self.get_project_repos(project)
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan project {project} : {e}.')
            return dict()
        logging.debug(f'Found repos for project {project} : {" ".join(repos)}')
        return {repo: self.scan_project_repo(project, repo) for repo in repos if self.matches_filter([project, repo])}

    def scan(self) -> dict:
        logging.info(f'Scanning {self.registry}')
        try:
            projects = self.get_projects()
        except urllib.error.HTTPError as e:
            logging.error(f'Not authorized to browse projects : {e}')
            return dict()
        logging.debug(f'Found projects: {" ".join(projects)}')
        return {project: self.scan_project(project) for project in projects if self.matches_filter([project])}

    def display(self, results: dict) -> None:
        if self.format == 'json':
            print(json.dumps(results, indent=4))
        elif self.format == 'text':
            for project, repos in results.items():
                print(f'{project}')
                for repo, artefacts in repos.items():
                    print(f'\t{repo}')
                    for a in sorted(artefacts, key=lambda x: x['time'], reverse=True):
                        print(f'\t\t{a["time"]} {a["digest"]} {" ".join(sorted(a["tags"]))}')
        else:
            raise NotImplementedError()

    def run(self) -> None:
        results = self.scan()
        self.display(results)


def main(argv: list[str] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    parser = ArgumentParser()
    parser.add_argument('-u', '--user', metavar='USER', default=os.environ.get('HARBOR_USER'))
    parser.add_argument('-p', '--password', metavar='PASS', default=os.environ.get('HARBOR_PASSWORD'))
    parser.add_argument('-r', '--registry', metavar='REG', default=os.environ.get('HARBOR_REGISTRY'))
    parser.add_argument('-l', '--level', choices=['debug', 'info', 'warning', 'error', 'critical'], default='warning')
    parser.add_argument('-f', '--format', choices=['text', 'json'], default='text')
    parser.add_argument('filters', nargs='*')
    args = parser.parse_args(argv)
    logging.basicConfig(format='%(levelname)s %(message)s', level=getattr(logging, args.level.upper()))
    if args.level == 'debug':
        handlers = [urllib.request.HTTPHandler(debuglevel=1), urllib.request.HTTPSHandler(debuglevel=1)]
        opener = urllib.request.build_opener(*handlers)
        urllib.request.install_opener(opener)
    app = App(user=args.user, password=args.password, registry=args.registry, fmt=args.format, filters=args.filters)
    try:
        app.run()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
