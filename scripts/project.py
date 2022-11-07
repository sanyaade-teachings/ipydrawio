""" important project paths

    this should not import anything not in py36+ stdlib, or any local paths
"""

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


import json
import os
import platform
import pprint
import re
import shutil
import subprocess
import sys
from pathlib import Path

print_ = pprint.pprint
console = None

HAS_SSORT = False

try:
    __import__("ssort")
    HAS_SSORT = True
except Exception:
    print("no big deal, but `ssort` is not available...")
    HAS_SSORT = False

try:
    import rich.console
    import rich.markdown

    console = rich.console.Console()
    print_ = console.print

except ImportError:
    pass

LITE_PREFIX = None
SOURCE_DATE_EPOCH = None

try:
    __import__("jupyterlite.manager")
    LITE_PREFIX = "demo_"
    SOURCE_DATE_EPOCH = (
        subprocess.check_output(["git", "log", "-1", "--format=%ct"])
        .decode("utf-8")
        .strip()
    )
except (ImportError, AttributeError, subprocess.CalledProcessError) as err:
    print_(err)
    pass


SKIPS = ["checkpoint", "pytest_cache", "patched-environment"]


def _clean(*paths_or_globs):
    cleaned = []
    for p_or_g in paths_or_globs:
        paths = [p_or_g] if isinstance(p_or_g, Path) else [*p_or_g]
        for p in paths:
            str_p = str(p)
            skipped = False
            for skip in SKIPS:
                if skip in str_p:
                    skipped = True
            if not skipped:
                cleaned += [p]
    return cleaned


def delete_some(*paths_or_globs):
    for p_or_g in paths_or_globs:
        paths = [p_or_g] if isinstance(p_or_g, Path) else [*p_or_g]
        for p in paths:
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()


_SESSION = None


# platform
PLATFORM = os.environ.get("FAKE_PLATFORM", platform.system())
WIN = PLATFORM == "Windows"
OSX = PLATFORM == "Darwin"
UNIX = not WIN
PREFIX = Path(sys.prefix)
ENC = dict(encoding="utf-8")
JSON_FMT = dict(indent=2, sort_keys=True)

BUILDING_IN_CI = bool(json.loads(os.environ.get("BUILDING_IN_CI", "0")))
TESTING_IN_CI = bool(json.loads(os.environ.get("TESTING_IN_CI", "0")))
CI_ARTIFACT = os.environ.get("CI_ARTIFACT", "wheel")
CI = bool(json.loads(os.environ.get("CI", "0")))
RTD = bool(json.loads(os.environ.get("READTHEDOCS", "0").lower()))


# test arg pass-throughs
ATEST_ARGS = json.loads(os.environ.get("ATEST_ARGS", "[]"))
ATEST_ATTEMPT = json.loads(os.environ.get("ATEST_ATTEMPT", "0"))
ATEST_RETRIES = int(os.environ.get("ATEST_RETRIES") or "0")
PYTEST_ARGS = json.loads(os.environ.get("PYTEST_ARGS", "[]"))
ATEST_PROCS = int(os.environ.get("ATEST_PROCS", "4"))

# find root
SCRIPTS = Path(__file__).parent.resolve()
ROOT = SCRIPTS.parent
PY_MAJOR = "".join(map(str, sys.version_info[:2]))

# demo
BINDER = ROOT / ".binder"
OVERRIDES = BINDER / "overrides.json"
POSTBUILD_PY = BINDER / "postBuild"
ENV_BINDER = BINDER / "environment.yml"

# top-level stuff
NODE_MODULES = ROOT / "node_modules"
PACKAGE = ROOT / "package.json"
PACKAGES = ROOT / "packages"
YARN_INTEGRITY = NODE_MODULES / ".yarn-integrity"
YARN_LOCK = ROOT / "yarn.lock"
DODO = ROOT / "dodo.py"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SETUP_CFG = ROOT / "setup.cfg"

# external URLs
# archive.org template
CACHE_EPOCH = 0
HTTP_CACHE = BUILD / ".requests-cache"


def A_O(archive_id, url, cache_bust=CACHE_EPOCH):
    return "https://web.archive.org/web/{}/{}#{}".format(archive_id, url, cache_bust)


DIA_FAQ = "https://www.diagrams.net/doc/faq"

FETCHED = BUILD / "fetched"

DIA_URLS = {
    FETCHED
    / "supported-url-parameters.html": (
        A_O(20210425055302, f"{DIA_FAQ}/supported-url-parameters")
    ),
    FETCHED / "embed-mode.html": (A_O(20200924053756, f"{DIA_FAQ}/embed-mode")),
    FETCHED
    / "configure-diagram-editor.html": (
        A_O(20210503071537, f"{DIA_FAQ}/configure-diagram-editor")
    ),
}


# ci
GH = ROOT / ".github"
CI_YML = GH / "workflows/ci.yml"
ENV_GH = GH / "environment.yml"
ENV_GH_CB = GH / "environment-conda-build.yml"
ENV_GH_CB_WIN = GH / "environment-conda-build-win.yml"

# tools
PY = ["python"]
PYM = [*PY, "-m"]
PIP = [*PYM, "pip"]
PIP_CHECK_IGNORE = "^(No broken|pylint|sphinx-rtd-theme) "

NPM = (
    shutil.which("npm")
    or shutil.which("npm.cmd")
    or shutil.which("npm.exe")
    or shutil.which("npm.bat")
)
JLPM = ["jlpm"]
LERNA = [*JLPM, "lerna"]
JLPM_INSTALL = [*JLPM, "--ignore-optional", "--prefer-offline"]
LAB_EXT = ["jupyter", "labextension"]
LAB = ["jupyter", "lab"]
PRETTIER = [str(NODE_MODULES / ".bin" / "prettier")]

# tests
EXAMPLES = ROOT / "notebooks"
EXAMPLE_IPYNB = _clean(EXAMPLES.rglob("*.ipynb"))

DIST_NBHTML = DIST / "nbsmoke"
ATEST = ROOT / "atest"
ATEST_DIO = _clean(ATEST.rglob("*.dio"), ATEST.rglob("*.dio.svg"))
ATEST_OUT = BUILD / "atest"
ATEST_OUT_XML = "output.xml"
ATEST_TEMPLATES = [*ATEST.rglob("*.robot.j2")]

# js packages
JS_NS = "deathbeds"
IPYDIO = PACKAGES / "ipydrawio"
TSCONFIGBASE = PACKAGES / "tsconfigbase.json"
TSCONFIG_TYPEDOC = PACKAGES / "tsconfig.typedoc.json"
TYPEDOC_JSON = PACKAGES / "typedoc.json"
TYPEDOC_CONF = [TSCONFIG_TYPEDOC, TYPEDOC_JSON]
NO_TYPEDOC = ["_meta", "ipydrawio-webpack"]

# so many js packages
JS_PKG_JSON = {p.parent.name: p for p in PACKAGES.glob("*/package.json")}

JS_PKG_DATA = {k: json.loads(v.read_text(**ENC)) for k, v in JS_PKG_JSON.items()}

JS_PKG_JSON_LABEXT = {
    k: v
    for k, v in JS_PKG_JSON.items()
    if JS_PKG_DATA[k].get("jupyterlab", {}).get("extension")
}

JS_LABEXT_PY_HOST = {
    k: JS_PKG_DATA[k]["jupyterlab"]["discovery"]["server"]["base"]["name"]
    for k, v in JS_PKG_JSON.items()
    if JS_PKG_DATA[k].get("jupyterlab", {}).get("discovery")
}

JS_PKG_NOT_META = {k: v for k, v in JS_PKG_JSON.items() if k.startswith("_")}


def _norm_js_version(pkg):
    """undo some package weirdness"""
    v = pkg["version"]
    final = ""
    # alphas, beta use dashes
    for dashed in v.split("-"):
        if final:
            final += "-"
        for dotted in dashed.split("."):
            if final:
                final += "."
            if re.findall(r"^\d+$", dotted):
                final += str(int(dotted))
            else:
                final += dotted
    return final


JS_TARBALL = {
    k: JS_PKG_JSON[k].parent
    / f"""{v["name"].replace('@', '').replace("/", "-")}-{_norm_js_version(v)}.tgz"""
    for k, v in JS_PKG_DATA.items()
    if k not in JS_PKG_NOT_META
}

JS_TSCONFIG = {
    k: v.parent / "src/tsconfig.json"
    for k, v in JS_PKG_JSON.items()
    if (v.parent / "src/tsconfig.json").exists()
}

JS_TSSRC = {
    k: sorted(
        [
            *(v.parent).rglob("*.ts"),
            *(v.parent / "src").rglob("*.tsx"),
        ]
    )
    for k, v in JS_TSCONFIG.items()
}

JS_TSBUILDINFO = {
    k: v.parent.parent / ".src.tsbuildinfo" for k, v in JS_TSCONFIG.items()
}

JS_STYLE = {
    k: sorted((v.parent / "style").glob("*.css"))
    for k, v in JS_PKG_JSON.items()
    if (v.parent / "style").exists()
}

JS_PY_SCRIPTS = {
    k: sorted((v.parent / "scripts").glob("*.py"))
    for k, v in JS_PKG_JSON.items()
    if (v.parent / "scripts").exists()
}

JS_SCHEMAS = {
    k: sorted((v.parent / "schema").glob("*.json"))
    for k, v in JS_PKG_JSON.items()
    if (v.parent / "schema").exists()
}

# special things for ipydrawio-webpack and friends
IPDWP = JS_PKG_JSON["ipydrawio-webpack"].parent
IPDWP_APP = IPDWP / "dio/js/app.min.js"
IPDWP_PY = (IPDWP / "scripts").rglob("*.py")
DRAWIO = IPDWP / "drawio"
IPDWP_LIB = IPDWP / "lib"
IPDWP_IGNORE = IPDWP / ".npmignore"
ALL_IPDWP_JS = IPDWP_LIB.glob("*.js")

IPDM_JS = JS_PKG_JSON["ipydrawio-mathjax"].parent
IPDM_JS_LIB = IPDM_JS / "lib"
ALL_IPDM_JS = IPDM_JS_LIB.glob("*.js")

IPDS_JS = JS_PKG_JSON["ipydrawio-stencils"].parent
IPDS_JS_LIB = IPDS_JS / "lib"
ALL_IPDS_JS = IPDS_JS_LIB.glob("*.js")

IPJT = JS_PKG_JSON["ipydrawio-jupyter-templates"].parent
IPJT_TMPL = IPJT / "tmpl"
IPJT_TMPL_DIO = _clean(
    IPJT_TMPL.rglob("*.dio"),
    IPJT_TMPL.rglob("*.dio.svg"),
)

PY_PACKAGES = ROOT / "py_packages"

PY_SETUP = {p.parent.name: p for p in sorted((ROOT / "py_packages").glob("*/setup.py"))}
PY_SRC = {k: sorted((v.parent / "src").rglob("*.py")) for k, v in PY_SETUP.items()}
PY_SETUP_CFG = {k: v.parent / "setup.cfg" for k, v in PY_SETUP.items()}

PY_VERSION = {
    "ipydrawio": JS_PKG_DATA["ipydrawio"]["version"],
    "ipydrawio-export": JS_PKG_DATA["ipydrawio-pdf"]["version"],
    "ipydrawio-widgets": JS_PKG_DATA["ipydrawio"]["version"],
    "ipydrawio-mathjax": JS_PKG_DATA["ipydrawio-mathjax"]["version"],
    "ipydrawio-stencils": JS_PKG_DATA["ipydrawio-stencils"]["version"],
}

IPD = PY_SETUP["ipydrawio"].parent
IPDE = PY_SETUP["ipydrawio-export"].parent
IPDW = PY_SETUP["ipydrawio-widgets"].parent
IPDM = PY_SETUP["ipydrawio-mathjax"].parent
IPDS = PY_SETUP["ipydrawio-stencils"].parent

IPDE_VENDOR = IPDE / "src/ipydrawio_export/vendor"
IPDE_DIE2 = IPDE_VENDOR / "draw-image-export2"
IPDE_DIE2_PACKAGE_JSON = IPDE_DIE2 / "package.json"
IPDE_DIE2_YARN_LOCK = IPDE_DIE2 / "yarn.lock"

IPDW_SRC = IPDW / "src/ipydrawio_widgets"
IPDW_DEPS = {
    JS_PKG_JSON["ipydrawio"]: IPDW_SRC / "js/package.json",
    JS_PKG_JSON["ipydrawio"].parent / "schema/plugin.json": IPDW_SRC / "js/plugin.json",
}

IPDM_STARTUP = JS_PKG_JSON["ipydrawio-mathjax"].parent / "dio/math/es5/startup.js"
IPDS_LICENSE = JS_PKG_JSON["ipydrawio-stencils"].parent / "dio/stencils/LICENSE"

PY_HAS_EXT = {IPD: True, IPDE: True, IPDW: False, IPDM: True, IPDS: True}

SERVER_EXT = {
    k: sorted(v.parent.glob("src/*/serverextension.py"))[0]
    for k, v in PY_SETUP.items()
    if sorted(v.parent.glob("src/*/serverextension.py"))
}

# package: [dependencies, targets]
JS_PKG_PACK = {
    k: [[v.parent / "package.json", *v.parent.glob("schema/*.json")], [v]]
    for k, v in JS_TARBALL.items()
}
[
    JS_PKG_PACK[k][0].append(v)
    for k, v in JS_TSBUILDINFO.items()
    if not k.startswith("_")
]
OK_PYSETUP = {k: BUILD / f"pysetup.{k}.ok" for k, v in PY_SETUP.items()}

PY_SETUP_DEPS = {
    IPD: lambda: [OK_PYSETUP["ipydrawio-widgets"]],
    IPDE: lambda: [OK_PYSETUP["ipydrawio"]],
    IPDW: lambda: [*IPDW_DEPS.values()],
    IPDM: lambda: [OK_PYSETUP["ipydrawio"], IPDM_STARTUP],
    IPDS: lambda: [OK_PYSETUP["ipydrawio"], IPDS_LICENSE],
}

PY_SDIST = {
    name: PY_PACKAGES / name / f"dist/{name}-{PY_VERSION[name]}.tar.gz"
    for name, version in PY_VERSION.items()
}

PY_WHEEL = {
    name: PY_PACKAGES
    / name
    / f"""dist/{name.replace("-", "_")}-{PY_VERSION[name]}-py3-none-any.whl"""
    for name, version in PY_VERSION.items()
}

PY_TEST_DEP = {}

# demo
RE_CONDA_FORGE_URL = r"/conda-forge/(.*/)?(noarch|linux-64|win-64|osx-64)/([^/]+)$"
CONDA_FORGE_RELEASE = "https://conda.anaconda.org/conda-forge"
FED_EXT_MARKER = "### FEDERATED EXTENSIONS ###"
DEMO = ROOT / "demo"
DEMO_FILES = DEMO / "files"
DEMO_CONFIG = DEMO / "jupyter_lite_config.json"
DEMO_REQS = DEMO / "requirements.txt"
DEMO_APPS = ["lab"]
DEMO_BUILD = BUILD / "demo"
DEMO_HASHES = DEMO_BUILD / "SHA256SUMS"
DEMO_CONTENTS_API = DEMO_BUILD / "api/contents/all.json"
DEMO_ARCHIVE = (
    DEMO_BUILD / f"""ipydrawio-lite-{JS_PKG_DATA["ipydrawio"]["version"]}.tgz"""
)
BUILD_WHEELS = BUILD / "wheels"
DEMO_WHEELS = DEMO / "pypi"
NOARCH_WHL = "py3-none-any.whl"
IGNORED_WHEELS = ["widgetsnbextension", "nbformat", "ipykernel", "pyolite"]
# sync swith jupyterlite
PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.21.1/full"
PYODIDE_PACKAGES = BUILD / "pyodide-packages.json"
DEMO_PATCHES = DEMO / "mocks"
PYOLITE_PACKAGES = {
    pyproj.parent: pyproj.parent
    / "dist/{}-{}-py3-none-any.whl".format(
        pyproj.parent.name,
        re.findall(
            r'''__version__ = "(.*)"''',
            next((pyproj.parent).glob("*/__init__.py")).read_text(encoding="utf-8"),
        )[0],
    )
    for pyproj in DEMO_PATCHES.glob("*/pyproject.toml")
}

# docs
SPHINX_ARGS = json.loads(os.environ.get("SPHINX_ARGS", "[]"))
DOCS_CONF = DOCS / "conf.py"
ENV_DOCS = DOCS / "environment.yml"
DOCS_BUILD = BUILD / "docs"
DOCS_BUILDINFO = DOCS_BUILD / ".buildinfo"
DOCS_MD = _clean(
    [
        p
        for p in DOCS.rglob("*.md")
        if not (p.parent.name == "ts" or p.parent.parent.name == "ts")
    ]
)
DOCS_DIO = _clean(DOCS.rglob("*.dio"), DOCS.rglob("*.dio.svg"))
DOCS_RST = _clean(DOCS.rglob("*.rst"))
DOCS_IPYNB = _clean(DOCS.rglob("*.ipynb"))
DOCS_SRC = _clean(DOCS_MD, DOCS_RST, DOCS_IPYNB)
DOCS_STATIC = DOCS / "_static"
ALL_DOCS_STATIC = [p for p in DOCS_STATIC.rglob("*") if not p.is_dir()]
DOCS_FAVICON_SVG = DOCS_STATIC / "icon.svg"
DOCS_FAVICON_ICO = DOCS_STATIC / "favicon.ico"
DOCS_TS = DOCS / "api/ts"
DOCS_TS_MYST_INDEX = DOCS_TS / "index.md"
DOCS_TS_MODULES = [
    ROOT / "docs/api/ts/modules" / f"deathbeds_{p.parent.name.replace('-','_')}.md"
    for p in JS_PKG_JSON.values()
    if p.parent.name not in NO_TYPEDOC
]

DOCS_RAW_TYPEDOC = BUILD / "typedoc"
DOCS_RAW_TYPEDOC_README = DOCS_RAW_TYPEDOC / "README.md"
MD_FOOTER = """
```
Copyright 2022 ipydrawio contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
"""

# collections, mostly for linting
ALL_PY = [
    *ATEST.rglob("*.py"),
    *BINDER.glob("*.py"),
    *IPDWP_PY,
    *PY_SETUP.values(),
    *SCRIPTS.glob("*.py"),
    *sum(JS_PY_SCRIPTS.values(), []),
    *sum(PY_SRC.values(), []),
    DODO,
    POSTBUILD_PY,
    DOCS_CONF,
]
ALL_YML = _clean(
    ROOT.glob("*.yml"),
    GH.rglob("*.yml"),
    BINDER.glob("*.yml"),
    DOCS.rglob("*.yml"),
)
ALL_PACKAGE_JSON = [PACKAGE, *JS_PKG_JSON.values()]
ALL_JSON = [
    *ROOT.glob("*.json"),
    *PACKAGES.glob("*/*.json"),
    *PACKAGES.glob("*/schema/*.json"),
    *ATEST.glob("fixtures/*.json"),
    *BINDER.glob("*.json"),
    *[
        p
        for p in DEMO.rglob("*.json")
        if "/_output/" not in str(p)
        and "/.cache/" not in str(p)
        and p not in [DEMO_CONFIG]
    ],
]
ALL_DIO = [*DOCS_DIO, *IPJT_TMPL_DIO, *ATEST_DIO]
ALL_MD = [*ROOT.glob("*.md"), *PACKAGES.glob("*/*.md"), *DOCS_MD]
ALL_SETUP_CFG = [SETUP_CFG, *PY_SETUP_CFG.values()]
ALL_JS = [PACKAGES / ".eslintrc.js"]
ALL_TS = sum(JS_TSSRC.values(), [])
ALL_SRC_CSS = [*sum(JS_STYLE.values(), [])]
ALL_CSS = [*ALL_SRC_CSS, *DOCS.rglob("*.css")]
ALL_ROBOT = [*ATEST.rglob("*.robot")]
ALL_PRETTIER = [*ALL_YML, *ALL_JSON, *ALL_MD, *ALL_TS, *ALL_CSS, *ALL_JS]
ALL_HEADERS = _clean(
    ALL_SETUP_CFG,
    ALL_PY,
    ALL_TS,
    ALL_CSS,
    ALL_JS,
    ALL_MD,
    ALL_YML,
    ALL_ROBOT,
)

ALL_DEMO_SOURCES = [
    d
    for d in ALL_DIO
    if "test" not in str(d.relative_to(ROOT)).lower()
    and ".doit" not in d.name
    and " " not in d.name
    and d.name not in ["A.dio"]
] + [*DOCS.glob("*.ipynb")]

ALL_DEMO_CONTENTS = {p: DEMO_FILES / p.name for p in sorted(ALL_DEMO_SOURCES)}

ESLINTRC = PACKAGES / ".eslintrc.js"

RFLINT_OPTS = sum(
    [
        ["--ignore", c]
        for c in [
            "FileTooLong",
            "LineTooLong",
            "RequireKeywordDocumentation",
            "RequireKeywordDocumentation",
            "TooFewKeywordSteps",
            "TooFewTestSteps",
            "TooManyTestSteps",
        ]
    ],
    [],
)

# drawio-derived
JS_PKG_PACK[IPDWP.name][0] += [
    IPDWP_IGNORE,
    IPDWP_APP,
    *ALL_IPDWP_JS,
]

JS_PKG_PACK[IPDM.name][0] += [IPDWP_IGNORE, IPDWP_APP, *ALL_IPDM_JS, IPDM_STARTUP]
JS_PKG_PACK[IPDS.name][0] += [IPDWP_IGNORE, IPDWP_APP, *ALL_IPDS_JS, IPDS_LICENSE]


# provisioning stuff
IPYDRAWIO_DATA_DIR = Path(sys.prefix) / "share/jupyter/ipydrawio_export"

# built files
OK_PIP_CHECK = BUILD / "pip.check.ok"
OK_INTEGRITY = BUILD / "integrity.ok"
OK_SUBMODULES = BUILD / "submodules.ok"
OK_BLACK = BUILD / "black.ok"
OK_FLAKE8 = BUILD / "flake8.ok"
OK_ISORT = BUILD / "isort.ok"
OK_SSORT = BUILD / "ssort.ok"
OK_LINT = BUILD / "lint.ok"
OK_ROBOTIDY = BUILD / "robot.tidy.ok"
OK_PYFLAKES = BUILD / "pyflakes.ok"
OK_PRETTIER = BUILD / "prettier.ok"
OK_ESLINT = BUILD / "eslint.ok"
OK_JS_BUILD_PRE = BUILD / "js.build.pre.ok"
OK_JS_BUILD = BUILD / "js.build.ok"
OK_PYTEST = {k: BUILD / f"pytest.{k}.ok" for k, v in PY_SETUP.items()}
OK_SERVEREXT = {k: BUILD / f"serverext.{k}.ok" for k, v in SERVER_EXT.items()}
OK_PROVISION = BUILD / "provision.ok"
OK_ROBOT_DRYRUN = BUILD / "robot.dryrun.ok"
OK_RFLINT = BUILD / "robot.rflint.ok"
OK_DIOLINT = BUILD / "dio.lint.ok"
OK_ATEST = BUILD / "atest.ok"
OK_CONDA_TEST = BUILD / "conda-build.test.ok"
OK_LINK_CHECK = BUILD / "pytest-check-links.ok"

OK_EXT_BUILD = {k: BUILD / f"ext.build.{k}.ok" for k in JS_LABEXT_PY_HOST}

PY_TEST_DEP.setdefault("ipydrawio-export", []).append(OK_PROVISION)

HASH_DEPS = [*PY_SDIST.values(), *PY_WHEEL.values(), *JS_TARBALL.values()]
SHA256SUMS = DIST / "SHA256SUMS"

# built artifacts
EXAMPLE_HTML = [DIST_NBHTML / p.name.replace(".ipynb", ".html") for p in EXAMPLE_IPYNB]

CMD_LIST_EXTENSIONS = ["jupyter", "labextension", "list"]

CMD_LAB = ["jupyter", "lab", "--no-browser", "--debug"]

# conda building
RECIPE = ROOT / "conda.recipe/meta.yaml"
CONDA_BLD = BUILD / "conda-bld"
CONDARC = GH / ".condarc"
# could be mambabuild
CONDA_BUILDERER = os.environ.get("CONDA_BUILDERER", "build")
CONDA_BUILD_ARGS = [
    "conda",
    CONDA_BUILDERER,
    "--override-channels",
    "-c",
    "conda-forge",
    "-c",
    "nodefaults",
]
CONDA_PKGS = {
    pkg: CONDA_BLD / f"noarch/{pkg}-{ver}-py_0.tar.bz2"
    for pkg, ver in PY_VERSION.items()
}

# env inheritance
ENV_INHERITS = {
    ENV_BINDER: [ENV_GH, ENV_DOCS],
    ENV_DOCS: [ENV_GH],
    ENV_GH_CB_WIN: [ENV_GH_CB],
}


def get_atest_stem(attempt=1, extra_args=None, browser=None):
    """get the directory in ATEST_OUT for this platform/apps"""
    browser = browser or "headlessfirefox"
    extra_args = extra_args or []

    stem = f"{PLATFORM}_{PY_MAJOR}_{browser}_{attempt}"

    if "--dryrun" in extra_args:
        stem += "_dry_run"

    return stem


def ensure_session():
    global _SESSION

    if _SESSION is None:
        try:
            import requests_cache

            _SESSION = requests_cache.CachedSession(cache_name=str(HTTP_CACHE))
        except ImportError:
            import requests

            _SESSION = requests.Session()


def fetch_one(url, path):
    import doit

    yield dict(
        uptodate=[doit.tools.config_changed({"url": url})],
        name=path.name,
        actions=[
            (doit.tools.create_folder, [HTTP_CACHE]),
            (doit.tools.create_folder, [path.parent]),
            (ensure_session, []),
            lambda: [path.write_bytes(_SESSION.get(url).content), None][-1],
        ],
        targets=[path],
    )


def patch_one_env(source, target):
    source_text = source.read_text(**ENC)
    name = re.findall(r"name: (.*)", source_text)[0]
    comment = f"  ### {name}-deps ###"
    old_target = target.read_text(**ENC).split(comment)
    new_source = source_text.split(comment)
    target.write_text(
        "\n".join(
            [
                old_target[0].strip(),
                comment,
                new_source[1],
                comment.rstrip(),
                old_target[2],
            ]
        ),
        **ENC,
    )


def typedoc_conf():
    typedoc = json.loads(TYPEDOC_JSON.read_text(**ENC))
    original_entry_points = sorted(typedoc["entryPoints"])
    new_entry_points = sorted(
        [
            str(
                (
                    p.parent
                    if (p.parent / "src/index.ts").exists()
                    else p.parent / "lib/index.d.ts"
                )
                .relative_to(PACKAGES)
                .as_posix()
            )
            for p in JS_PKG_JSON.values()
            if p.parent.name not in NO_TYPEDOC
        ]
    )

    if json.dumps(original_entry_points) != json.dumps(new_entry_points):
        typedoc["entryPoints"] = new_entry_points
        TYPEDOC_JSON.write_text(json.dumps(typedoc, **JSON_FMT), **ENC)

    tsconfig = json.loads(TSCONFIG_TYPEDOC.read_text(**ENC))
    original_references = tsconfig["references"]
    new_references = sum(
        [
            [
                {"path": f"./{p.parent.name}/src"},
                {"path": f"./{p.parent.name}"},
            ]
            for p in JS_PKG_JSON.values()
            if p.parent.name not in NO_TYPEDOC
        ],
        [],
    )

    if json.dumps(original_references) != json.dumps(new_references):
        tsconfig["references"] = new_references
        TSCONFIG_TYPEDOC.write_text(json.dumps(tsconfig, **JSON_FMT), **ENC)


def mystify():
    """unwrap monorepo docs into per-module docs"""
    if DOCS_TS.exists():
        shutil.rmtree(DOCS_TS)

    for doc in sorted(DOCS_RAW_TYPEDOC.rglob("*.md")):
        if doc.parent == DOCS_RAW_TYPEDOC:
            continue
        if doc.name == "README.md":
            continue
        doc_text = doc.read_text(**ENC)
        doc_lines = doc_text.splitlines()

        # rewrite doc and write back out
        out_doc = DOCS_TS / doc.relative_to(DOCS_RAW_TYPEDOC)
        if not out_doc.parent.exists():
            out_doc.parent.mkdir(parents=True)

        out_text = "\n".join([*doc_lines[1:], ""]).replace("README.md", "index.md")
        out_text = re.sub(
            r"## Table of contents(.*?)\n## ",
            "\n## ",
            out_text,
            flags=re.M | re.S,
        )
        out_text = out_text.replace("/src]", "]")
        out_text = re.sub("/src$", "", out_text, flags=re.M)
        out_text = re.sub(
            r"^((Implementation of|Overrides|Inherited from):)",
            "_\\1_",
            out_text,
            flags=re.M | re.S,
        )
        out_text = re.sub(
            r"^Defined in: ([^\n]+)$",
            "_Defined in:_ `\\1`",
            out_text,
            flags=re.M | re.S,
        )

        out_text += MD_FOOTER

        out_doc.write_text(out_text, **ENC)

    DOCS_TS_MYST_INDEX.write_text(
        "\n".join(
            [
                "# `@deathbeds/ipydrawio`\n",
                "```{toctree}",
                ":maxdepth: 1",
                ":caption: Modules",
                ":glob:",
                "modules/*",
                "```",
                "```{toctree}",
                ":maxdepth: 1",
                ":caption: Interfaces",
                ":glob:",
                "interfaces/*",
                "```",
                "```{toctree}",
                ":caption: Classes",
                ":maxdepth: 1",
                ":glob:",
                "classes/*",
                "```",
                MD_FOOTER,
            ]
        ),
        **ENC,
    )


def pip_check():
    proc = subprocess.Popen([*PIP, "check"], stdout=subprocess.PIPE)
    proc.wait()
    out = proc.stdout.read().decode("utf-8")
    print(out)
    lines = [
        line
        for line in out.splitlines()
        if line.strip() and not re.findall(PIP_CHECK_IGNORE, line)
    ]
    return not len(lines)


# utilities
def _echo_ok(msg):
    def _echo():
        print(msg, flush=True)
        return True

    return _echo


def _ok(task, ok):
    task.setdefault("targets", []).append(ok)
    task["actions"] = [
        lambda: [ok.exists() and ok.unlink(), True][-1],
        *task["actions"],
        lambda: [ok.parent.mkdir(exist_ok=True), ok.write_text("ok", **ENC), True][-1],
    ]
    return task


def _show(*args, **kwargs):
    import rich.markdown

    for arg in args:
        print_(arg()) if callable(arg) else print_(arg)
    for kw, kwarg in kwargs.items():
        print_(rich.markdown.Markdown(f"# {kw}") if console else kw)
        print_(kwarg()) if callable(kwarg) else print_(kwarg)


def _copy_one(src, dest):
    if not src.exists():
        return False
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)


def _lite(lite_actions, extra_args=[]):
    lite = ["jupyter", "lite"]
    args = ["--source-date-epoch", SOURCE_DATE_EPOCH]

    try:
        from jupyter_server_mathjax.app import STATIC_ASSETS_PATH as MATHJAX_DIR
    except Exception:
        MATHJAX_DIR = None

    if MATHJAX_DIR:
        args += ["--mathjax-dir", str(MATHJAX_DIR)]

    for act in lite_actions:
        act_args = list(map(str, [*lite, act, *args, *extra_args]))
        if subprocess.call(act_args, cwd=DEMO) != 0:
            print("FAILED", *act_args)
            return False


def _sync_lite_config(from_env, to_json, marker, extra_federated, extra_pyolite):
    """use conda list to derive tarball names"""
    raw_lock = subprocess.check_output(["conda", "list", "--explicit"])
    ext_packages = [
        p.strip().split(" ")[0]
        for p in from_env.read_text(**ENC).split(marker)[1].split(" - ")
        if p.strip()
    ]

    federated_extensions = sorted(
        ["../" + str(extra.relative_to(ROOT).as_posix()) for extra in extra_federated]
    )
    piplite_urls = [
        "../" + str(extra.relative_to(ROOT).as_posix()) for extra in extra_pyolite
    ]

    for raw_url in sorted(raw_lock.decode("utf-8").splitlines()):
        try:
            label, subdir, pkg = re.findall(RE_CONDA_FORGE_URL, raw_url)[0]
        except IndexError:
            continue

        if label:
            # TODO: haven't looked into this
            continue

        for ext in ext_packages:
            if pkg.startswith(ext):
                federated_extensions += ["/".join([CONDA_FORGE_RELEASE, subdir, pkg])]

    config = json.loads(to_json.read_text(**ENC))

    config["LiteBuildConfig"].update(
        federated_extensions=federated_extensions,
        piplite_urls=piplite_urls,
    )

    to_json.write_text(json.dumps(config, **JSON_FMT), **ENC)

    subprocess.call([*PRETTIER, "--write", to_json])


def fetch_pyodide_packages():
    import urllib.request

    url = f"{PYODIDE_URL}/repodata.json"
    print("fetching pyodide packages from", url)
    with urllib.request.urlopen(url) as response:
        packages = json.loads(response.read().decode("utf-8"))
    PYODIDE_PACKAGES.parent.mkdir(exist_ok=True, parents=True)
    PYODIDE_PACKAGES.write_text(json.dumps(packages, **JSON_FMT), **ENC)


def fetch_wheels():
    BUILD_WHEELS.mkdir(exist_ok=True, parents=True)
    DEMO_WHEELS.mkdir(exist_ok=True, parents=True)
    pyodide_pkgs = json.loads(PYODIDE_PACKAGES.read_text(encoding="utf-8"))
    pyodide_norm_names = [k.lower().replace("-", "_") for k in pyodide_pkgs["packages"]]
    subprocess.check_call(
        ["pip", "download", "-r", str(DEMO_REQS), "--prefer-binary"],
        cwd=str(BUILD_WHEELS),
    )
    for pkg in sorted(BUILD_WHEELS.glob("*")):
        norm_name = pkg.name.split("-")[0].lower()
        if not pkg.name.endswith(NOARCH_WHL):
            continue
        if norm_name in pyodide_norm_names or norm_name in IGNORED_WHEELS:
            continue
        dest = DEMO_WHEELS / pkg.name

        if dest.exists():
            if pkg.stat().st_mtime > dest.stat().st_mtime():
                dest.unlink()
            else:
                continue

        shutil.copy2(pkg, dest)


def template_one(src, dest):
    import jinja2

    template = jinja2.Template(src.read_text(**ENC))
    if not dest.parent.exists():
        dest.parent.mkdir()
    if dest.exists():
        dest.unlink()
    dest.write_text(template.render(P=globals()))


def build_one_flit(py_pkg):
    """attempt to build one package with flit: on RTD, allow doing a build in /tmp"""
    import tempfile

    print(f"[{py_pkg.name}] trying in-tree build...", flush=True)
    args = ["flit", "--debug", "build", "--setup-py"]

    try:
        subprocess.check_call(args, cwd=str(py_pkg))
    except subprocess.CalledProcessError:
        if not RTD:
            print(f"[{py_pkg.name}] ... in-tree build failed, not on ReadTheDocs")
            return False
        print(
            f"[{py_pkg.name}] ... in-tree build failed, trying build in tempdir...",
            flush=True,
        )
        py_dist = py_pkg / "dist"
        if py_dist.exists():
            shutil.rmtree(py_dist)

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            py_tmp = tdp / py_pkg.name
            shutil.copytree(py_pkg, py_tmp)
            subprocess.call(args, cwd=str(py_tmp))
            shutil.copytree(py_tmp / "dist", py_dist)


# Late environment hacks
os.environ.update(
    CONDARC=str(CONDARC),
    IPYDRAWIO_DATA_DIR=str(IPYDRAWIO_DATA_DIR),
    PIP_DISABLE_PIP_VERSION_CHECK="1",
)
