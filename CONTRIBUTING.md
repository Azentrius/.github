# Contributing

Bug reports, ideas and pull requests for Azentrius projects are welcome. This is the default for
every repository of the organisation that has no `CONTRIBUTING.md` of its own; where a repository
has one, that one applies.

Security problems do not belong in public issues: report them privately as described in
[SECURITY.md](SECURITY.md). For a larger change, open an issue first so we can agree on the
approach.

## Requirements for a change

- **English in the repository.** Code, comments, docs, commit messages and pull requests are in
  English; translations are the only exception.
- **Tests** for new behaviour, and the repository's checks green (its README says how to run them).
- **SPDX header** `SPDX-License-Identifier: Apache-2.0` in every new source file.
- **Versions and changelog** are the maintainer's. Describe user-visible changes in your pull
  request; the maintainer adds them to `CHANGELOG.md`.
- **No private data.** No secrets, tokens, passwords, host names, IP addresses or other real data
  from your systems in issues, pull requests, tests or fixtures.

## Pull requests

- Open them against `main`. `main` is protected: every change goes through a pull request and is
  squash-merged once the checks are green.
- The title becomes the commit on `main`: short, imperative, English, without a version number.
- Keep one topic per pull request and fill in the template: what and why, how it was tested.

## License

Azentrius projects are licensed under the Apache License 2.0; contributions are accepted under the
same license. Third-party material keeps its own license and is listed in the repository's `NOTICE`;
new third-party material needs a compatible license and an entry there.
