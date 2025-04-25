import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class HarborApi:

    @staticmethod
    def activate_urllib_debug_logging() -> None:
        handlers = [urllib.request.HTTPHandler(debuglevel=1), urllib.request.HTTPSHandler(debuglevel=1)]
        opener = urllib.request.build_opener(*handlers)
        urllib.request.install_opener(opener)

    def __init__(self, registry_fqdn: str, username: str, password: str):
        if registry_fqdn is None:
            raise ValueError('registry_fqdn must be defined')
        if username is None:
            raise ValueError('username is required')
        if password is None:
            raise ValueError('password is required')
        self.registry_fqdn = registry_fqdn
        self.basic_token = b64encode(f'{username}:{password}'.encode()).decode()

    def authenticated_get(self, url: str):
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Basic {self.basic_token}')
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)

    def projects(self) -> list[dict]:
        url = f'https://{self.registry_fqdn}/api/v2.0/projects'
        return self.authenticated_get(url)

    def project_repos(self, project: str) -> list[dict]:
        url = f'https://{self.registry_fqdn}/api/v2.0/projects/{project}/repositories'
        return self.authenticated_get(url)

    def project_repo_artifacts(self, project: str, repo: str) -> list[dict]:
        # According to Harbor API documentation : https://demo.goharbor.io/devcenter-api-2.0
        #   If the repository name contains slash, encode it twice over with URL encoding
        #   e.g. a/b -> a%2Fb -> a%252Fb
        repo = urllib.parse.quote(repo, safe='')  # first force-encodes '/' by excluding it from safe characters
        repo = urllib.parse.quote(repo)  # then once more, to stop the server from reinterpreting it as '/'
        url = f'https://{self.registry_fqdn}/api/v2.0/projects/{project}/repositories/{repo}/artifacts'
        return self.authenticated_get(url)


class HarborLs:

    def __init__(self, *, registry_fqdn: str, user: str, password: str, filters: list[str] = None) -> None:
        self.api = HarborApi(registry_fqdn, user, password)
        self.filters = [] if filters is None else [_filter.split('/') for _filter in filters]

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

    def get_projects(self) -> list[str]:
        return [item['name'] for item in self.api.projects()]

    def get_project_repos(self, project: str) -> list[str]:
        return [item['name'].split('/', maxsplit=1)[1] for item in self.api.project_repos(project)]

    def get_project_repo_artifacts(self, project: str, repo: str) -> list[dict]:
        return [{'time': artifact['push_time'], 'digest': artifact['digest'],
                 'tags': [] if artifact['tags'] is None else [tag['name'] for tag in artifact['tags']]} for artifact in
                self.api.project_repo_artifacts(project, repo)]

    def scan_project_repo_artifacts(self, project: str, repo: str) -> list[dict]:
        logging.debug(f'Scanning {self.api.registry_fqdn} project {project} repo {repo}')
        try:
            artifacts = self.get_project_repo_artifacts(project, repo)
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan project {project} repo {repo} artifacts : {e}.')
            return []
        logging.info(f'Found {len(artifacts)} artifacts for project {project} repo {repo}')
        return artifacts

    def scan_project_repos(self, project: str) -> dict:
        logging.debug(f'Scanning {self.api.registry_fqdn} project {project}')
        try:
            repos = self.get_project_repos(project)
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan project {project} repos : {e}.')
            return dict()
        details = '' if len(repos) == 0 else f': {" ".join(repos)}'
        logging.info(f'Found {len(repos)} repos for project {project}{details}')
        with ThreadPoolExecutor() as executor:
            results = executor.map(partial(self.scan_project_repo_artifacts, project), repos)
        return dict(zip(repos, results))

    def ls(self) -> dict:
        logging.debug(f'Scanning {self.api.registry_fqdn}')
        try:
            projects = self.get_projects()
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan registry {self.api.registry_fqdn} projects : {e}.')
            return dict()
        details = '' if len(projects) == 0 else f': {" ".join(projects)}'
        logging.info(f'Found {len(projects)} projects{details}')
        with ThreadPoolExecutor() as executor:
            results = executor.map(self.scan_project_repos, projects)
        return dict(zip(projects, results))
