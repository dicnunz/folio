# Folio email comparison

## Scope and testing method

The email comparison evaluates locally constructed Folio email messages and distinguishes message composition from SMTP transmission. The tests send no real email and require no credentials or external services.

The evaluation uses Python's standard-library `email` + `smtplib` approach as the baseline. The comparison focuses on message structure and creation reliability rather than provider-specific delivery behavior.

## Implementation mechanics

| Candidate | Message construction | SMTP transmission | Attachment support | Validation of required fields | External service requirement |
|---|---|---|---|---|---|
| Python stdlib `email` + `smtplib` | Strong; explicit MIME handling | Strong and standard | Good | Strong when application code performs validation | Runtime requires an SMTP server |
| Provider-specific API client (example: SendGrid, SES) | Usually more opinionated but simpler in app code | Provider API handles transmission | Good | Varies by service SDK | Requires a real credentialed account and network access |
| Mail-sending library (example: Flask-Mail) | Good, but app-layer abstraction | Usually wraps SMTP or provider integration | Good | Depends on library design | Usually still requires external service |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| Python stdlib `email` + `smtplib` | Python standard library | None | Python 3.11.x |
| Provider API client | Varies by provider | Varies by package | The evaluation did not exercise this candidate |
| Mail-sending library | Varies by library | Varies by package | The evaluation did not exercise this candidate |

## Functional test results

| Checklist item | Python stdlib | Provider API (design analysis) | Mail library (design analysis) |
|---|:---:|:---:|:---:|
| From/To/Subject construction | Pass | N/A | N/A |
| Plain-text body | Pass | N/A | N/A |
| HTML body | Pass | N/A | N/A |
| Attachment support | Pass | N/A | N/A |
| MIME/message validity | Pass | N/A | N/A |
| Validation of required fields | Pass | N/A | N/A |
| Simulated send flow | Pass (local construction only) | N/A | N/A |

## Candidate comparison summary

| Candidate | Implementation complexity | Delivery portability | Credential requirement | Maintainability | Folio fit |
|---|---|---|---|---|---|
| Python stdlib `email` + `smtplib` | Low | High | Moderate at runtime | High | High |
| Provider API client | Moderate | High | High | Moderate | Moderate |
| Mail library wrapper | Moderate | Moderate | Moderate-High | Moderate | Moderate |

## Version details

- Python: 3.11.x

## Notes on interpretation

Measured observations: the standard library successfully constructed valid message objects, included plain-text and HTML alternatives, and supported attachment creation without external dependencies.

Documentation-derived facts: provider and framework mail libraries help when an application requires delivery automation, but the libraries introduce external service and credential configuration requirements. The evaluation deliberately excluded external services and credentials to avoid sending real email.

Engineering judgments: the standard-library approach provides the best practical baseline for Folio because the approach runs locally and offers deterministic, transparent behavior. The standard library supports message construction and local validation well, while environment configuration controls SMTP delivery at runtime.

## Selection: Python stdlib `email` + `smtplib`

**Rationale:** The evidence confirms the Python standard-library approach as the baseline. The approach constructs Folio reminder emails and generated-report attachments simply, explicitly, and reliably without introducing provider-specific dependencies or credentialed external systems.
