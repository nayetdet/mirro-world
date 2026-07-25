# Mirro-World

Mirro-World is an automated service that mirrors GitHub repositories to GitLab on a schedule, keeping projects synchronized with minimal manual effort.

## Features

- Lists owned GitHub repositories through the API.
- Processes repositories from the oldest to the most recently pushed.
- Optionally includes forks and archived repositories.
- Automatically creates GitLab projects while preserving the source visibility.
- Prevents overwriting existing GitLab projects when their refs do not match the expected mirror.
- Keeps local bare clones in `data/mirrors` to speed up future synchronizations.
- Continues processing other repositories when an individual mirror fails.
- Stores execution logs in `data/logs`.
- Runs locally with `uv` or as a scheduled Docker Swarm service.

## Requirements

- Python 3.14+
- `git` available in `PATH`
- A GitHub token with access to the repositories to be mirrored
- A GitLab token with permission to create projects and push to the target namespace

Scheduled deployments also require Docker Swarm to be enabled.

## Configuration

Create an `.env` file from the example:

```bash
cp .env.example .env
```

Then set the variables:

| Variable | Description |
| --- | --- |
| `TZ` | Time zone used by the application and scheduler. |
| `CRON` | Cron expression used by the Docker Swarm deployment. |
| `GITHUB_USERNAME` | GitHub username that owns the repositories. Kept for environment identification. |
| `GITHUB_TOKEN` | Token used to query the GitHub API and clone repositories. |
| `GITLAB_TOKEN` | Token used to authenticate with GitLab, create projects, and push mirrors. |
| `GITLAB_URL` | GitLab instance URL. Defaults to `https://gitlab.com`. |
| `GITLAB_NAMESPACE_ID` | Numeric ID of the target GitLab namespace. |
| `MIRRORS_INCLUDE_FORKS` | Whether forks should also be mirrored. |
| `MIRRORS_INCLUDE_ARCHIVED` | Whether archived repositories should also be mirrored. |
| `MIRRORS_OVERRIDE` | Disables GitLab ref safety checks and forces the destination to be overwritten. Defaults to `false`; use with extreme caution. |

### Tokens

Create separate tokens for GitHub and GitLab. Save each token when it is created,
because these services usually do not display it again after the creation screen
is closed.

#### GitHub

Use a fine-grained personal access token whenever possible:

1. Open `GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens`.
2. Click `Generate new token`.
3. Select the repository owner under `Resource owner`.
4. Under `Repository access`, choose either:
   - `All repositories`, to mirror all owned repositories.
   - `Only select repositories`, to limit the mirror to specific repositories.
5. Grant these repository permissions:
   - `Contents: Read-only`, required to clone repositories over HTTPS.
   - `Metadata: Read-only`, usually required to query repository metadata.
6. Generate the token and set its value as `GITHUB_TOKEN`.

For a classic personal access token:

- Use the `repo` scope for private repositories.
- Use `public_repo` for public repositories only.

The GitHub token does not need write access because this project only reads and
clones source repositories.

#### GitLab

Create a GitLab personal access token:

1. Open `GitLab > Preferences > Access tokens`.
2. Enter a name, such as `mirro-world`.
3. Set an expiration date that matches your security policy.
4. Grant these scopes:
   - `api`, required to authenticate with the API, locate the namespace, and create projects.
   - `write_repository`, required to push mirrors with `git push --mirror`.
5. Generate the token and set its value as `GITLAB_TOKEN`.

Set `GITLAB_NAMESPACE_ID` to the numeric ID of the user or group where mirrored
projects will be created. To find it, open the target user or group page in
GitLab. The ID appears in the namespace details and, for groups, under
`Settings > General`.

The token owner must have permission to create projects and push to the target
namespace. In GitLab groups, this usually means being an `Owner` or `Maintainer`,
or using a group setting that allows members to create projects.

For example, to run every Monday at midnight:

```env
CRON='0 0 * * 1'
```

## Local installation

Install the dependencies:

```bash
make install
```

Or directly with `uv`:

```bash
uv sync --all-groups --all-packages
```

## Local execution

With `.env` configured, run:

```bash
uv run python -m mirro_world.main
```

The command also initializes file-based logging. During execution, the
application:

1. Checks that `git` is installed.
2. Fetches owned repositories from GitHub.
3. Resolves the configured GitLab namespace.
4. Creates the destination project when necessary.
5. Continues only when an existing GitLab project is empty or its refs match the expected mirror.
6. Clones or updates the local mirror in `data/mirrors`.
7. Pushes the mirror to GitLab with `git push --mirror`.

If a push fails because of protected GitLab branches, the application only tries
to force the push when `MIRRORS_OVERRIDE=true`. In that mode, it enables
`allow_force_push` on the project's protected branches and retries the push once.
Without `MIRRORS_OVERRIDE`, the push is rejected. This prevents accidental
overwrites and keeps the behavior explicit.

To prevent accidental overwrites, a non-empty GitLab project is accepted only
when its refs match the last local clone stored in `data/mirrors`. This allows
GitLab to be updated after a `git push --force` on GitHub because GitLab still
matches the last known mirror state. On a new installation, when no local clone
exists yet, the GitLab project is accepted only when its refs match the current
GitHub refs.

### Safety override

`MIRRORS_OVERRIDE=false` is the default and should remain enabled during normal
operation.

`MIRRORS_OVERRIDE=true` bypasses ref protection and allows `git push --mirror` to
be retried even when the GitLab project uses protected branches. This setting is
extremely dangerous: it can delete, move, or overwrite branches and tags in a
different GitLab project with the same name. In practice, it confirms that you
accept replacing the destination with the GitHub state.

Enable `MIRRORS_OVERRIDE=true` only temporarily during a controlled run, then
set it back to `false`.

Logs are stored in:

```text
data/logs/
```

## Deploy

There are two supported deployment options: Docker Compose with Docker Swarm,
or Kubernetes with Helm.

### Docker Compose / Swarm

The image is published to GitHub Container Registry:

```text
ghcr.io/nayetdet/mirro-world:latest
```

The `docker-compose.yml` file runs the application as a scheduled Docker Swarm
service using `crazy-max/swarm-cronjob`. The main service starts with
`replicas: 0`; the cronjob creates executions according to `CRON`.

Configure the environment and deploy:

```bash
cp .env.example .env
./deploy.sh
```

Custom Compose and environment files can also be provided:

```bash
./deploy.sh \
  --docker-compose docker-compose.yml \
  --env-file .env
```

The deployment script checks both files, initializes Docker Swarm when needed,
and deploys the `mirro-world` stack.

### Kubernetes / Helm

The chart is published to the GitHub Container Registry as an OCI artifact:

```text
oci://ghcr.io/nayetdet/charts/mirro-world
```

Install a chart version with:

```bash
helm install mirro-world oci://ghcr.io/nayetdet/charts/mirro-world \
  --version 0.1.0 \
  --namespace mirro-world \
  --create-namespace
```

The chart creates the CronJob and PersistentVolumeClaim used by the
application. By default, it also creates an `ExternalSecret`; alternatively,
you can point the CronJob at an existing Kubernetes `Secret`. Configure the
deployment by creating a values file and passing it with `--values`, for
example:

```bash
helm upgrade --install mirro-world \
  oci://ghcr.io/nayetdet/charts/mirro-world \
  --version 0.1.0 \
  --namespace mirro-world \
  --create-namespace \
  --values values.production.yaml
```

The consumed Secret name is configured with `secret.name`. Enable exactly one
source:

```yaml
secret:
  enabled: false
  name: mirro-world

externalSecret:
  enabled: true
  storeName: ""
  refreshInterval: 1h
  remoteKey: mirro-world
```

When `externalSecret.enabled` is `true`, replace the empty `storeName` with
the name of the `ClusterSecretStore` to use.

To use a Secret that already exists in the namespace, set
`secret.enabled: true` and `externalSecret.enabled: false`. The chart only
references that Secret; it does not create or modify it.

The Helm workflow runs when files under `k8s/mirro-world/` change on `main` or
when it is started manually. Increment `version` in
`k8s/mirro-world/Chart.yaml` before publishing a new chart version.

For a private GHCR package, configure the registry credentials in Argo CD or
authenticate Helm with a GitHub token that has `read:packages`.

## Persistent data

By default, the application uses the `data` directory at the project root:

```text
data/
├── logs/      # Execution logs
└── mirrors/   # Bare clones used for incremental synchronization
```

This directory should not be committed.

## Structure

```text
src/mirro_world/
├── clients/      # GitHub and GitLab clients
├── core/         # Mirror synchronization logic
├── logging.py    # Logging configuration
├── utils/        # URL and repository name helpers
├── main.py       # Main workflow
└── settings.py   # Environment-based configuration
```

## License

This project is licensed under GPL-3.0-or-later. See the [`LICENSE`](LICENSE)
file for details.
