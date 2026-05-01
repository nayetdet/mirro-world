import gitlab
from typing import List
from gitlab import Gitlab
from github.Repository import Repository
from gitlab.v4.objects import Namespace, Project
from loguru import logger
from mirro_world.settings import settings

class GitlabClient:
    def __init__(self) -> None:
        self.__client: Gitlab = Gitlab(url=settings.GITLAB_URL.rstrip("/"), private_token=settings.GITLAB_TOKEN.get_secret_value())
        self.__client.auth()

    def get_namespace(self) -> Namespace:
        if settings.GITLAB_NAMESPACE_ID:
            return self.__client.namespaces.get(settings.GITLAB_NAMESPACE_ID)

        gitlab_namespace_path: str = settings.GITLAB_NAMESPACE.strip()
        try: return self.__client.namespaces.get(gitlab_namespace_path)
        except gitlab.exceptions.GitlabGetError:
            gitlab_namespaces: List[Namespace] = self.__client.namespaces.list(search=gitlab_namespace_path.rsplit("/", maxsplit=1)[-1], get_all=True)
            for gitlab_namespace in gitlab_namespaces:
                if gitlab_namespace.full_path == gitlab_namespace_path:
                    return gitlab_namespace
            raise RuntimeError(f"GitLab namespace not found: {gitlab_namespace_path}")

    def get_project(self, github_repository: Repository, gitlab_project_path: str, gitlab_namespace: Namespace) -> Project:
        try:
            gitlab_project_full_path: str = f"{gitlab_namespace.full_path}/{gitlab_project_path}"
            gitlab_project: Project = self.__client.projects.get(gitlab_project_full_path)
            logger.info("GitLab project already exists: {}", gitlab_project.path_with_namespace)
            return gitlab_project
        except gitlab.exceptions.GitlabGetError as error:
            if error.response_code != 404:
                raise
        return self.create_project(github_repository, gitlab_project_path, gitlab_namespace)

    def create_project(self, github_repository: Repository, gitlab_project_path: str, gitlab_namespace: Namespace) -> Project:
        logger.info("Creating GitLab project...")
        return self.__client.projects.create(
            {
                "name": github_repository.name,
                "path": gitlab_project_path,
                "visibility": "private" if github_repository.private else "public",
                "namespace_id": gitlab_namespace.id
            }
        )
