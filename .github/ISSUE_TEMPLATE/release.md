---
name: Release
about: Prepare for a release
labels: maintenance
---

- [ ] merge all outstanding PRs
- [ ] ensure the versions have been bumped (check with `doit test:integrity`)
- [ ] ensure the CHANGELOG is up-to-date
  - [ ] move the new release to the top of the stack
- [ ] validate on binder
- [ ] validate on ReadTheDocs
- [ ] wait for a successful build of `master`
- [ ] download the `dist` archive and unpack somewhere (maybe a fresh `dist`)
- [ ] create a new release through the GitHub UI
  - [ ] paste in the relevant CHANGELOG entries
  - [ ] upload the artifacts
- [ ] actually upload to npm.com, pypi.org
  ```bash
  cd dist
  twine upload *.tar.gz *.whl
  npm login
  npm publish deathbeds-*-$VERSION.tgz
  npm logout
  ```
- [ ] postmortem
  - [ ] handle `conda-forge` feedstock tasks
  - [ ] validate on binder via simplest-possible gists
  - [ ] bump to next development version
  - [ ] bump the `CACHE_EPOCH`
  - [ ] rebuild `yarn.lock`
  - [ ] update release procedures with lessons learned
  - [ ] update the [discourse thread][discourse]

[discourse]:
  https://discourse.jupyter.org/t/ipydrawio-diagrams-in-jupyterlab-with-pages-layers-widgets-pdf-export

<!--
# Copyright 2022 ipydrawio contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
-->
