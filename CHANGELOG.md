# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-01

### Added

- Sales analytics: `summary`, `by-hour`, `by-product`, `by-category`, `compare`, `stats`
- Receipt management: `list`, `show`, `search` (by client name)
- Catalog browsing: `list`, `find`, `show`, `by-category`
- Payment analytics: `summary`, `mix` (percentage distribution)
- Meta queries: `categories list`, `stores list`, `registers list`
- Data sync: `sync sales` — export raw documents to JSON
- API diagnostics: `inspect auth`, `inspect rate-limit`
- Built-in date aliases: `today`, `yesterday`, `7d`, `this-week`, `last-week`, `this-month`, `last-month`, `last-same-weekday`
- Output formats: `--format json|table|md`
- Store and register filtering via `--store` and `--register` flags
- Credential loading from environment variables, `.env`, and `.secrets` files
