from github.Repository import Repository
from slugify import slugify

class RepositoryUtils:
    @staticmethod
    def get_repo_path(repo: Repository, full_name: bool = False) -> str:
        return slugify(
            text=repo.name if not full_name else repo.full_name,
            lowercase=True,
            regex_pattern=r"[^A-Za-z0-9._-]+"
        ) or "repo"
