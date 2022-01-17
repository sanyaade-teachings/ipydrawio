"""ipydrawio repo integrity tests"""

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

import configparser
import json
import re
import sys
import tarfile
from pathlib import Path

import jsonpointer
import pytest
import yaml

if True:
    sys.path.append(str(Path(__file__).parent.parent))
    from scripts import project as P


@pytest.fixture
def the_changelog():
    return (P.ROOT / "CHANGELOG.md").read_text(**P.ENC)


@pytest.fixture
def the_demo_config():
    return json.loads(P.DEMO_CONFIG.read_text(**P.ENC))


@pytest.fixture
def the_ci():
    return yaml.safe_load(P.CI_YML.read_text(**P.ENC))


@pytest.fixture
def the_pythons(the_ci):
    return sorted(
        the_ci["jobs"]["test"]["strategy"]["matrix"]["python-version"],
        key=lambda x: list(map(int, x.split("."))),
    )


@pytest.fixture
def the_min_python(the_pythons):
    return the_pythons[0]


@pytest.mark.parametrize(
    "pkg,version",
    [
        *[[k, v] for k, v in P.PY_VERSION.items()],
        *[
            [v["name"], v["version"]]
            for k, v in P.JS_PKG_DATA.items()
            if not k.startswith("_")
        ],
    ],
)
def test_changelog(pkg, version, the_changelog):
    """are the current versions referenced in the CHANGELOG?"""
    version_string = f"### {pkg} {version}"
    assert version_string in the_changelog, version_string


def test_drawio_versions():
    """is the drawio version up-to-date with the submodule?"""
    dv = (P.IPDWP / "drawio/VERSION").read_text(encoding="utf-8")
    pdv = P.JS_PKG_DATA[P.IPDWP.name]["version"]
    assert pdv.startswith(dv), "drawio version out of sync"


def test_recipe_versions():
    """is the conda recipe version correct"""
    assert f"""version = "{P.IPD_VERSION}" """ in P.RECIPE.read_text(**P.ENC)


@pytest.mark.parametrize(
    "pointer,value",
    [
        ["output_archive", f"../build/demo/{P.DEMO_ARCHIVE.name}"],
        [
            "federated_extensions/0",
            f"""../{P.PY_WHEEL["ipydrawio"].relative_to(P.ROOT)}""",
        ],
        [
            "piplite_urls/0",
            f"""../{P.PY_WHEEL["ipydrawio-widgets"].relative_to(P.ROOT)}""",
        ],
    ],
)
def test_demo_paths(the_demo_config, pointer, value):
    """are the version-specific paths correct in the demo configuration?"""
    assert (
        jsonpointer.resolve_pointer(the_demo_config, f"/LiteBuildConfig/{pointer}")
        == value
    )


@pytest.mark.parametrize("path", P.ALL_HEADERS)
def test_headers(path):
    """are the license headers correct?"""
    text = path.read_text(encoding="utf-8")
    assert (
        "Copyright 2022 ipydrawio contributors" in text
    ), f"{path.relative_to(P.ROOT)} needs copyright header"
    assert (
        'Licensed under the Apache License, Version 2.0 (the "License");' in text
    ), f"{path.relative_to(P.ROOT)} needs license header"


@pytest.mark.parametrize("key,tarball", [*P.JS_TARBALL.items(), *P.PY_SDIST.items()])
def test_tarball(key, tarball):
    """do the distributons have key metadata files?"""
    with tarfile.open(str(tarball), "r") as tar:
        all_names = list(tar.getnames())
        licenses = [p for p in all_names if "LICENSE.txt" in p]
        assert licenses, f"{key} doesn't have LICENSE"
        readmes = [p for p in all_names if "README.md" in p]
        assert readmes, f"{key} doesn't have README"


@pytest.mark.parametrize("path", [p for p in P.ALL_SETUP_CFG if p.parent != P.ROOT])
def test_setup_cfg_pythons(path, the_pythons, the_min_python):
    """are the python versions correctly noted?"""
    cfg = configparser.ConfigParser()
    cfg.read_file(path.open())
    python_requires = cfg["options"]["python_requires"]
    assert python_requires == f">={the_min_python}"
    for the_py in the_pythons:
        classifier = f"Programming Language :: Python :: {the_py}"
        assert classifier in cfg["metadata"]["classifiers"]


@pytest.mark.parametrize(
    "path,upstream,version",
    [
        [P.PY_SETUP_CFG["ipydrawio"], P.IPDW.name, P.PY_VERSION["ipydrawio-widgets"]],
        [P.PY_SETUP_CFG["ipydrawio-export"], P.IPD.name, P.PY_VERSION["ipydrawio"]],
    ],
)
def test_setup_cfg_version(path, upstream, version):
    cfg = configparser.ConfigParser()
    cfg.read_file(path.open())
    install_requires = cfg["options"]["install_requires"]
    spec = f"{upstream} =={version}"
    assert (
        spec in install_requires
    ), f"{spec} not in {path.parent.name}: {install_requires}"


@pytest.mark.parametrize(
    "path,py_count",
    [
        [P.RECIPE, 8],
        [P.ENV_BINDER, 1],
    ],
)
def test_yaml_pythons(path, py_count, the_min_python):
    yaml_text = path.read_text(**P.ENC)
    matches = re.findall(f"- python >={the_min_python}", yaml_text)
    assert len(matches) == py_count, [len(matches), py_count]
