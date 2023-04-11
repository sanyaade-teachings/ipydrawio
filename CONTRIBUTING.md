# CONTRIBUTING

## Help Wanted

- tackling [roadmap] issues
- improving testing
- improving (self-hosted) documentation
- improving the binder demo
- improving [continuous integration][ci] and [developer experience][dodo]

[roadmap]: https://github.com/deathbeds/ipydrawio/blob/main/docs/ROADMAP.ipynb
[ci]: https://github.com/deathbeds/ipydrawio/blob/main/.github/workflows/ci.yml
[dodo]: https://github.com/deathbeds/ipydrawio/blob/main/dodo.py

## Prerequisites

- `doit >=0.32`
- `jupyterlab >=3,<4`
- `nodejs >=18,<19`
- `python >=3.8`

### Recommended: `mamba`

- Get [Miniforge/Mambaforge](https://github.com/conda-forge/miniforge/releases)

```bash
mamba env update --file .github/environment.yml
source activate ipydrawio
```

> or use the demo environment in `.binder`

## Get to a working Lab

```bash
doit
```

## Start JupyterLab

```bash
doit serve:lab
```

### Start JupyterLite

```bash
doit serve:demo
```

## Prepare a Release

```bash
doit dist
```

## Do everything

```bash
doit all
```

## Updating drawio

- update the `version` in `packages/ipydrawio-webpack/package.json`
- update dependencies in other `package.json`

```bash
pushd packages/ipydrawio-webpack/drawio
git fetch
git checkout v<the new version>
popd
doit dist
```

- validate everything looks good!

## Releasing

- Start a [release] issue on GitHub
  - Follow the checklist

[release]: https://github.com/deathbeds/ipydrawio/issues/new?template=release.md

<!--
Copyright 2023 ipydrawio contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
