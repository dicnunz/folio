# Folio development and collaboration workflow comparison

## Scope and testing method

The collaboration comparison evaluates Git hosting and collaboration choices based on Folio's expected workflow. The evaluation team did not create a remote repository or change any accounts; the evaluation compares documented capabilities and workflows rather than live-hosted implementations.

The comparison covers these candidates:

- GitHub
- GitLab
- Bitbucket (optional comparison value only)

## Implementation mechanics

| Candidate | Repository hosting | Issues/task tracking | Branch model | Pull requests | Review and merge workflows | CI support | Free-tier fit |
|---|---|---|---|---|---|---|---|
| GitHub | Very strong | Very strong | Very strong | Very strong | Very strong | Very strong | Very strong |
| GitLab | Very strong | Very strong | Very strong | Very strong | Very strong | Very strong | Strong |
| Bitbucket | Strong | Strong | Strong | Strong | Strong | Strong | Moderate |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| GitHub | Git + GitHub account | `git --version` | The evaluation team validated local Git behavior without a remote account |
| GitLab | Git + GitLab account | `git --version` | The evaluation team validated local Git behavior without a remote account |
| Bitbucket | Git + Bitbucket account | `git --version` | The evaluation team validated local Git behavior without a remote account |

## Functional test results

| Workflow item | GitHub | GitLab | Bitbucket |
|---|:---:|:---:|:---:|
| Local Git repository works | Pass | Pass | Pass |
| Platform supports the branch workflow | Pass (documentation) | Pass (documentation) | Pass (documentation) |
| Pull request model | Pass (documentation) | Pass (documentation) | Pass (documentation) |
| Issue/task tracking | Pass (documentation) | Pass (documentation) | Pass (documentation) |
| CI integration | Pass (documentation) | Pass (documentation) | Pass (documentation) |
| Free-tier suitability | Pass | Pass | Pass |

## Candidate comparison summary

| Candidate | Learning curve | Team workflow fit | Documentation value | Folio fit |
|---|---|---|---|---|
| GitHub | Low | Very High | Very High | Very High |
| GitLab | Low-Moderate | High | High | High |
| Bitbucket | Moderate | Moderate | Moderate | Moderate |

## Version details

- Git: the evaluation team validated local repository behavior in the workspace
- The evaluation team assessed platform features through documented capability comparisons rather than live account exercises.

## Notes on interpretation

Measured observations: the local Git workflow functions correctly in the project environment, and all candidate platforms accommodate the expected feature flow.

Documentation-derived facts: all three platforms support Git-based hosting, issues, branches, pull requests, and CI. Ecosystem familiarity, team fit, and free-tier ergonomics create the primary differences among the platforms.

Engineering judgments: GitHub offers the strongest practical choice for a two-person senior-design team because GitHub aligns well with common classroom and project workflows, provides mature documentation, and enjoys broad familiarity among students and faculty.

## Proposed Folio workflow

`Issue/Task -> Feature Branch -> Development -> Local Tests -> Commit -> Push -> Pull Request -> Peer Review -> Merge`

## Recommended lightweight conventions

- Branch naming: `feature/<short-name>`, `fix/<issue-name>`, `docs/<topic>`
- Commit messages: concise, action-oriented, and issue-linked where possible
- Pull requests: include a short rationale, changed files, and test evidence
- Review before merge: require at least one human review for nontrivial changes
- Link issues/tasks: include issue numbers in the branch name or PR description
- Keep `main` working: avoid merging untested or partially complete changes

## Selection: GitHub

**Rationale:** GitHub offers the strongest practical fit for Folio's collaboration workflow. Students and faculty know GitHub well, and GitHub provides mature issue and pull-request tooling, integrates well with CI, and matches the expected lightweight senior-design team process.
