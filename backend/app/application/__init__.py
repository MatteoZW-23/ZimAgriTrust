"""
Application layer — orchestrates use cases.

May import from `app.domain` only. Never from `app.infrastructure`,
`app.api`, `app.services`, `app.models`, or `app.db`.
Adapters are injected via the ports defined in `app.application.ports`.
"""
