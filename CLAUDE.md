# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An AWS Lambda (packaged as a Docker container) that fetches an `.ipynb` file over HTTP and returns rendered HTML, fronted by an API Gateway v2 HTTP API at `api-{dev|prod}.synapse.org/nbconvert`. The Synapse web portal calls it to preview notebook files. The entire application is ~50 lines (`nbconvert/service.py`); most of the repo is deployment infrastructure.

## Layout

- `nbconvert/` — the Lambda: `service.py` (handler), its own pinned `requirements.txt`, and the `Dockerfile`. This directory is the Docker build context; only `service.py` and `requirements.txt` are copied into the image.
- `cdk/nbconvert_stack.py` — the whole infrastructure definition (Lambda function, HTTP API, JWT authorizer, custom domain, access logs).
- `app.py` + `cdk.json` — CDK entrypoint (`cdk.json` sets `app: python3 app.py`).
- Root `requirements.txt` — CDK-only deps. Do not add Lambda runtime deps here; they go in `nbconvert/requirements.txt`.
- `event.json` — sample API Gateway event payload for local invocation.

Note: the `nbconvert/` directory shadows the PyPI `nbconvert` package name when importing from the repo root. Run/import `service.py` from inside `nbconvert/`, not from the repo root.

## Commands

```bash
# Setup (CDK deps only; the Lambda's deps live in the container)
pip install -r requirements.txt -r requirements-dev.txt

# Lint / pre-commit (this is what CI runs on PRs)
pre-commit install
pre-commit run --all-files

# Synthesize / diff the stack
cdk synth --context fct_stack=dev
cdk diff --context fct_stack=dev

# Deploy (see Deployment below before doing this)
cdk deploy --region us-east-1 --profile <profile> --context fct_stack=[dev|prod]

# Build & invoke the Lambda container locally
docker build --platform linux/amd64 -t nbconvert-lambda ./nbconvert
docker run --rm -p 9000:8080 nbconvert-lambda
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @event.json
```

There are no tests in the repo (`requirements-dev.txt` pins `pytest`, but no test files exist). CI's "test" job is `pre-commit`, not pytest. If you add tests, `pytest tests/` is the assumed convention (`cdk.json`'s watch config already excludes a `tests` directory).

## The `fct_stack` context variable

Everything environment-specific keys off the `--context fct_stack=` value (defaults to `dev` in `nbconvert_stack.py`). It selects, in one place each: the ACM certificate ARN, the custom domain (`api-{fct_stack}.synapse.org`), the Lambda/function names, the CORS allowlist (dev gets only `dev.synapse.org`; prod gets `www`/`staging`/`tst`), and the JWT issuer (`https://repo-prod.{fct_stack}.sagebase.org/auth/v1`). When adding environment-varying config, extend the existing `if fct_stack == 'prod'` branches rather than introducing a new mechanism.

Certificate ARNs and the Synapse OAuth client ID are hardcoded constants in `cdk/nbconvert_stack.py` — they must be updated there when endpoints or certs change.

## Auth and access control

Routes are protected by an `HttpJwtAuthorizer` validating Synapse-issued JWTs. The Lambda handler itself does no authorization — it will fetch and render any URL passed in the `file` query parameter. Requests larger than 25MB (checked via `Content-Length`) are rejected with 400.

## Deployment

Deploys are automated by GitHub Actions (`.github/workflows/main.yaml` → `build.yaml`), which assumes an OIDC role and runs `cdk deploy`:

- push to `develop` → dev account `449435941126`
- push to `master` → prod account `325565585839`

`master` is this repo's default branch and its production branch; `develop` is the integration branch. Merging to `master` deploys to prod, so PRs generally target `develop`. Prefer letting CI deploy; run `cdk deploy` manually only for testing against a personal/dev account.
