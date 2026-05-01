# Mirro-World

Projeto que mantém repositórios do GitHub espelhados no GitLab de forma automática.

## Recursos

- Lista repositórios próprios do GitHub via API.
- Permite incluir ou ignorar forks.
- Permite incluir ou ignorar repositórios arquivados.
- Cria projetos no GitLab automaticamente, preservando a visibilidade pública ou
  privada do repositório de origem.
- Mantém clones bare locais em `data/mirrors` para acelerar sincronizações
  futuras.
- Registra logs de execução em `data/logs`.
- Pode rodar localmente com `uv` ou como serviço agendado em Docker Swarm.

## Requisitos

- Python 3.14+
- `uv`
- `git` disponível no `PATH`
- Token do GitHub com acesso aos repositórios que serão espelhados
- Token do GitLab com permissão para criar projetos e fazer push no namespace de
  destino

Para deploy agendado, também é necessário Docker com Swarm habilitado.

## Configuração

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Depois preencha as variáveis:

| Variável | Descrição |
| --- | --- |
| `TZ` | Fuso horário usado pela aplicação e pelo agendador. |
| `CRON` | Expressão cron usada pelo deploy em Docker Swarm. |
| `GITHUB_USERNAME` | Nome do usuário GitHub dono dos repositórios. Mantido na configuração para identificação do ambiente. |
| `GITHUB_TOKEN` | Token usado para consultar a API e clonar repositórios do GitHub. |
| `GITLAB_TOKEN` | Token usado para autenticar no GitLab, criar projetos e enviar mirrors. |
| `GITLAB_URL` | URL da instância GitLab. O padrão é `https://gitlab.com`. |
| `GITLAB_NAMESPACE_ID` | ID numérico do namespace de destino no GitLab. |
| `MIRRORS_INCLUDE_FORKS` | Define se forks também serão espelhados. |
| `MIRRORS_INCLUDE_ARCHIVED` | Define se repositórios arquivados também serão espelhados. |

### Tokens

Crie tokens separados para GitHub e GitLab. Salve o valor exibido na criação,
porque os serviços normalmente não mostram o token novamente depois que a tela é
fechada.

#### GitHub

Use um fine-grained personal access token sempre que possível:

1. Acesse `GitHub > Settings > Developer settings > Personal access tokens >
   Fine-grained tokens`.
2. Clique em `Generate new token`.
3. Em `Resource owner`, selecione o usuário dono dos repositórios.
4. Em `Repository access`, escolha:
   - `All repositories`, para espelhar todos os repositórios próprios.
   - `Only select repositories`, para limitar o mirror a uma lista específica.
5. Em `Repository permissions`, conceda:
   - `Contents: Read-only`, necessário para clonar os repositórios por HTTPS.
   - `Metadata: Read-only`, normalmente obrigatório e usado para consultar os
     metadados dos repositórios.
6. Gere o token e copie o valor para `GITHUB_TOKEN`.

Se usar um classic personal access token:

- Para espelhar repositórios privados, use o escopo `repo`.
- Para espelhar apenas repositórios públicos, `public_repo` é suficiente.

O token do GitHub não precisa de permissão de escrita, porque este projeto só lê
e clona os repositórios de origem.

#### GitLab

Crie um personal access token no GitLab:

1. Acesse `GitLab > Preferences > Access tokens`.
2. Informe um nome, por exemplo `mirro-world`.
3. Defina uma data de expiração compatível com sua política de segurança.
4. Marque os escopos:
   - `api`, necessário para autenticar na API, localizar o namespace e criar
     projetos.
   - `write_repository`, necessário para enviar o mirror com `git push
     --mirror`.
5. Gere o token e copie o valor para `GITLAB_TOKEN`.

Preencha `GITLAB_NAMESPACE_ID` com o ID numérico do usuário ou grupo onde os
projetos espelhados serão criados. Para encontrar esse valor no GitLab, abra a
página do usuário ou grupo de destino; o ID aparece nos detalhes do namespace.
Em grupos, ele também aparece em `Settings > General`.

A conta dona do token precisa ter permissão nesse namespace para criar projetos e
fazer push nos projetos criados. Em grupos do GitLab, isso normalmente significa
ser `Owner` ou `Maintainer`, ou ter uma configuração do grupo que permita criação
de projetos por membros.

Exemplo de agendamento para rodar toda segunda-feira à meia-noite:

```env
CRON='0 0 * * 1'
```

## Instalação local

Instale as dependências:

```bash
make install
```

Ou diretamente com `uv`:

```bash
uv sync --all-groups --all-packages
```

## Execução local

Com o `.env` configurado, rode:

```bash
uv run python -m mirro_world.main
```

O comando acima também inicializa o logging em arquivo. Durante a execução, a
aplicação:

1. Valida se o `git` está instalado.
2. Busca os repositórios próprios no GitHub.
3. Resolve o namespace configurado no GitLab.
4. Cria o projeto de destino quando necessário.
5. Clona ou atualiza o mirror local em `data/mirrors`.
6. Envia o mirror para o GitLab com `git push --mirror`.

Os logs ficam em:

```text
data/logs/
```

## Docker

A imagem é publicada no GitHub Container Registry pelo workflow de CI:

```text
ghcr.io/nayetdet/mirro-world:latest
```

O `docker-compose.yml` foi preparado para Docker Swarm usando
`crazy-max/swarm-cronjob`. O serviço principal começa com `replicas: 0`; o
cronjob cria execuções conforme a expressão definida em `CRON`.

Faça o deploy:

```bash
./deploy.sh
```

Também é possível informar arquivos customizados:

```bash
./deploy.sh --docker-compose docker-compose.yml --env-file .env
```

O script:

1. Verifica se o arquivo Compose existe.
2. Verifica se o arquivo de ambiente existe.
3. Inicializa o Docker Swarm caso ele ainda não esteja ativo.
4. Publica a stack `mirro-world`.

## Dados persistidos

Por padrão, a aplicação usa o diretório `data` na raiz do projeto:

```text
data/
├── logs/      # Arquivos de log por execução
└── mirrors/   # Clones bare usados para sincronização incremental
```

Esse diretório não deve ser versionado.

## Estrutura

```text
src/mirro_world/
├── clients/      # Clientes GitHub e GitLab
├── core/         # Lógica de sincronização do mirror
├── logging.py    # Configuração de logs
├── utils/        # Helpers para URLs e nomes de repositórios
├── main.py       # Fluxo principal
└── settings.py   # Configuração via variáveis de ambiente
```

## CI

O workflow em `.github/workflows/ci.yml` constrói e publica a imagem Docker no
GitHub Container Registry quando há push na branch `main` com mudanças em código,
Dockerfile, dependências ou workflow.

## Licença

Este projeto está licenciado sob GPL-3.0-or-later. Consulte o arquivo
[`LICENSE`](LICENSE) para mais detalhes.
