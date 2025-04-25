import json
import logging
import urllib.error
import urllib.request
from base64 import b64encode


class HarborApi:

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

    def project_repo_artefacts(self, project: str, repo: str) -> list[dict]:
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
        return [item['name'].split('/')[1] for item in self.api.project_repos(project)]

    def get_project_repo_artefacts(self, project: str, repo: str) -> list[dict]:
        return [{'time': artefact['push_time'], 'digest': artefact['digest'],
                 'tags': [] if artefact['tags'] is None else [tag['name'] for tag in artefact['tags']]} for artefact in
                self.api.project_repo_artefacts(project, repo)]

    def scan_project_repo_artefacts(self, project: str, repo: str) -> list[dict]:
        logging.info(f'Scanning {self.api.registry_fqdn} / {project} / {repo}')
        try:
            artefacts = self.get_project_repo_artefacts(project, repo)
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan project {project} repo {repo} artefacts : {e}.')
            return []
        return artefacts

    def scan_project_repos(self, project: str) -> dict:
        logging.info(f'Scanning {self.api.registry_fqdn} / {project}')
        try:
            repos = self.get_project_repos(project)
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan project {project} repos : {e}.')
            return dict()
        logging.debug(f'Found repos for project {project} : {" ".join(repos)}')
        return {repo: self.scan_project_repo_artefacts(project, repo) for repo in repos if
                self.matches_filter([project, repo])}

    def ls(self) -> dict:
        logging.info(f'Scanning {self.api.registry_fqdn}')
        try:
            projects = self.get_projects()
        except urllib.error.HTTPError as e:
            logging.warning(f'Could not scan registry {self.api.registry_fqdn} projects : {e}.')
            return dict()
        logging.debug(f'Found projects: {" ".join(projects)}')
        return {project: self.scan_project_repos(project) for project in projects if self.matches_filter([project])}
