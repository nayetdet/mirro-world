from typing import Dict
from git import Git, Repo
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

    @staticmethod
    def get_repo_refs(path: str, remote: bool) -> Dict[str, str]:
        refs: Dict[str, str] = {}
        output: str = Git().ls_remote(path) if remote else Repo(path).git.for_each_ref("--format=%(objectname)\t%(refname)", "refs")
        for line in output.splitlines():
            object_id, ref_name = line.split(maxsplit=1)
            if ref_name.startswith("refs/") and "^{}" not in ref_name:
                refs[ref_name] = object_id
        return refs
