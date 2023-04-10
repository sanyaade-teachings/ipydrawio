"""automation for ipydrawio.

> see https://pydoit.org/tutorial_1.html#incremental-computation

see what you can do

    doit list --status --all | sort

do basically everything to get ready for a release

    doit all

maybe before you push

    doit -n8 lint
"""

# Copyright 2023 ipydrawio contributors
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

import os
import shutil
import subprocess
import time
from collections import defaultdict
from hashlib import sha256

import doit
from doit.action import CmdAction
from doit.tools import PythonInteractiveAction, config_changed

import scripts.project as P

DOIT_CONFIG = {
    "backend": "sqlite3",
    "verbosity": 2,
    "par_type": "thread",
    "default_tasks": ["setup"],
}


def task_all():
    """Do _everything_ (except start long-running servers)."""
    return {
        "uptodate": [lambda: False],
        "task_dep": ["check"],
        "file_dep": [
            *[P.OK_CONDA_TEST / f"{name}.ok" for name in P.CONDA_PKGS],
            *P.OK_PYTEST.values(),
            P.DOCS_BUILDINFO,
            P.OK_ATEST,
            P.OK_INTEGRITY,
            P.OK_LINK_CHECK,
            P.OK_PROVISION,
            P.SHA256SUMS,
        ],
        "actions": [
            (P._show, ["nothing left to do"], {"shasums": P.SHA256SUMS.read_text}),
        ],
    }


def task_fetch():
    """Fetch local copies of key configuration documentation."""
    for path, url in P.DIA_URLS.items():
        yield P.fetch_one(url, path)


def task_dist():
    """Create a minimum viable release product."""
    file_dep = [P.SHA256SUMS]
    if not P.BUILDING_IN_CI:
        file_dep += [P.OK_INTEGRITY, P.OK_LINT]
    return {
        "uptodate": [lambda: False],
        "file_dep": file_dep,
        "actions": [lambda: print(P.SHA256SUMS.read_text())],
    }


def task_env():
    """Sync environments."""
    if P.RTD:
        return

    for env, inherits in P.ENV_INHERITS.items():
        yield {
            "name": f"""{env.relative_to(P.ROOT)}:{':'.join([str(inh.relative_to(P.ROOT)) for inh in inherits])}""",
            "file_dep": [*inherits, P.YARN_INTEGRITY],
            "actions": [(P.patch_one_env, [inh, env]) for inh in inherits]
            + [["jlpm", "prettier", "--list-different", "--write", env]],
            "targets": [env],
        }


def task_submodules():
    """Ensure submodules are available."""
    subs = subprocess.check_output(["git", "submodule"]).decode("utf-8").splitlines()

    def _clean():
        """Clean drawio, as it gets patched in-place."""
        if any(x.startswith("-") for x in subs) and P.DRAWIO.exists():
            shutil.rmtree(P.DRAWIO)

    return P._ok(
        {
            "uptodate": [config_changed({"subs": subs})],
            "actions": [
                _clean,
                ["git", "submodule", "update", "--init", "--recursive"],
            ],
        },
        P.OK_SUBMODULES,
    )


def task_setup():
    """Perform general steps to get ready for development, testing, or releasing."""
    if not (P.CI and P.YARN_INTEGRITY.exists()):
        yield {
            "name": "js",
            "file_dep": [P.PACKAGE, P.OK_SUBMODULES]
            + ([P.YARN_LOCK] if P.YARN_LOCK.exists() else []),
            "actions": [
                [*P.JLPM, "--prefer-offline", "--ignore-optional"],
            ],
            "targets": [P.YARN_INTEGRITY],
        }

    if not P.TESTING_IN_CI:
        yield {
            "name": "js:ipde",
            "file_dep": [P.IPDE_DIE2_PACKAGE_JSON, P.YARN_INTEGRITY],
            "targets": [P.IPDE_DIE2_YARN_LOCK],
            "actions": [
                CmdAction(
                    [*P.JLPM, "--prefer-offline", "--ignore-optional"],
                    shell=False,
                    cwd=P.IPDE_DIE2,
                ),
            ],
        }

    for pkg, pkg_setup in P.PY_SETUP.items():
        # TODO: refactor
        ext_deps = [
            (
                P.JS_PKG_JSON[ext].parent
                / P.JS_PKG_DATA[ext]["jupyterlab"]["outputDir"]
            ).resolve()
            / "package.json"
            for ext, mod in P.JS_LABEXT_PY_HOST.items()
            if mod == pkg_setup.parent.name
        ]

        if P.TESTING_IN_CI:
            ci_af = {"wheel": P.PY_WHEEL[pkg], "sdist": P.PY_SDIST[pkg]}[P.CI_ARTIFACT]
            dist_af = P.DIST / ci_af.name

            yield P._ok(
                {
                    "name": f"py:{pkg}",
                    "file_dep": [dist_af],
                    "actions": [
                        [
                            *P.PIP,
                            "install",
                            "-vv",
                            "--ignore-installed",
                            "--no-deps",
                            dist_af,
                        ],
                    ],
                },
                P.OK_PYSETUP[pkg],
            )
        else:
            extra_deps = P.PY_SETUP_DEPS[pkg_setup.parent]()

            actions = [
                CmdAction(
                    [
                        *P.PIP,
                        "install",
                        "-e",
                        ".",
                        "--no-deps",
                        "-vv",
                    ],
                    shell=False,
                    cwd=pkg_setup.parent,
                ),
            ]

            if P.PY_HAS_EXT.get(pkg_setup.parent):
                actions += [
                    CmdAction(
                        [
                            *P.LAB_EXT,
                            "develop",
                            "--debug",
                            "--overwrite",
                            ".",
                        ],
                        shell=False,
                        cwd=pkg_setup.parent,
                    ),
                ]

            yield P._ok(
                {
                    "name": f"py:{pkg}",
                    "file_dep": [
                        pkg_setup,
                        P.PY_SETUP_CFG[pkg],
                        *ext_deps,
                        *extra_deps,
                    ],
                    "actions": actions,
                },
                P.OK_PYSETUP[pkg],
            )

    yield P._ok(
        {
            "name": "pip:check",
            "file_dep": [*P.OK_PYSETUP.values()],
            "actions": [P.pip_check],
        },
        P.OK_PIP_CHECK,
    )

    base_ext_args = [
        "jupyter",
        "serverextension",
        "enable",
        "--sys-prefix",
        "--py",
    ]
    for ext, ext_py in P.SERVER_EXT.items():
        enable_args = [*base_ext_args, ext_py.parent.name]

        if P.TESTING_IN_CI:
            enable_args = ["echo", "'(installed by pip)'"]

        yield P._ok(
            {
                "name": f"ext:{ext}",
                "doc": f"ensure {ext} is a serverextension",
                "file_dep": [ext_py, P.OK_PIP_CHECK],
                "actions": [
                    enable_args,
                    ["jupyter", "serverextension", "list"],
                ],
            },
            P.OK_SERVEREXT[ext],
        )


def task_lint():
    """Format all source files."""
    if P.TESTING_IN_CI or P.BUILDING_IN_CI:
        return

    rel_py = [p.relative_to(P.ROOT) for p in P.ALL_PY]
    black_dep = []
    if P.HAS_SSORT:
        black_dep += [P.OK_SSORT]
        yield P._ok(
            {
                "name": "ssort",
                "file_dep": [
                    *P.ALL_PY,
                ],
                "actions": [["ssort", *rel_py]],
            },
            P.OK_SSORT,
        )
    yield P._ok(
        {
            "name": "black",
            "file_dep": [*P.ALL_PY, *black_dep],
            "actions": [["black", "--quiet", *rel_py]],
        },
        P.OK_BLACK,
    )
    yield P._ok(
        {
            "name": "ruff",
            "file_dep": [*P.ALL_PY, P.OK_BLACK],
            "actions": [["ruff", *rel_py]],
        },
        P.OK_RUFF,
    )

    prettier_args = [
        "jlpm",
        "--silent",
        "prettier",
        "--list-different",
        "--write",
    ]

    if P.CI:
        yield P._ok(
            {
                "name": "prettier",
                "file_dep": [
                    P.YARN_INTEGRITY,
                    *[p for p in P.ALL_PRETTIER if P != P.DEMO_CONFIG],
                ],
                "actions": [[*prettier_args, *P.ALL_PRETTIER]],
            },
            P.OK_PRETTIER,
        )
    else:
        pretty_parents = defaultdict(list)
        [pretty_parents[p.parent.relative_to(P.ROOT)].append(p) for p in P.ALL_PRETTIER]
        pretty_tasks = []

        for path in P.ALL_PRETTIER:
            if path.name != "package.json":
                continue
            pretty_name = f"prettier:package.json:{path.parent.relative_to(P.ROOT)}"
            pretty_tasks += [f"lint:{pretty_name}"]
            yield {
                "name": pretty_name,
                "file_dep": [path, P.YARN_INTEGRITY],
                "actions": [["jlpm", "prettier-package-json", "--write", path]],
            }

        for parent, paths in pretty_parents.items():
            name = f"prettier:{parent}"
            pretty_tasks += [f"lint:{name}"]

            yield {
                "name": name,
                "file_dep": [P.YARN_INTEGRITY, *paths],
                "actions": [[*prettier_args, *paths]],
            }

        yield P._ok(
            {
                "name": "prettier",
                "file_dep": [P.YARN_INTEGRITY, *P.ALL_PRETTIER],
                "task_dep": pretty_tasks,
                "actions": [["echo", "OK"]],
            },
            P.OK_PRETTIER,
        )

    # yield P._ok(
    #     dict(
    #             P.YARN_INTEGRITY,
    #             *P.ALL_TS,
    #             P.OK_PRETTIER,
    #             P.ESLINTRC,
    #             P.TSCONFIGBASE,
    #         ],
    #     ),
    #     P.OK_ESLINT,

    dio_tasks = []

    yield P._ok(
        {
            "name": "black:jupyter",
            "file_dep": P.EXAMPLE_IPYNB + P.DOCS_IPYNB,
            "actions": [
                ["black", *P.EXAMPLE_IPYNB, *P.DOCS_IPYNB],
                ["nbqa", "ruff", "--fix", *P.EXAMPLE_IPYNB, *P.DOCS_IPYNB],
            ],
        },
        P.OK_BLACK_JUPYTER,
    )

    yield P._ok(
        {
            "name": "nqqa:ruff",
            "file_dep": P.EXAMPLE_IPYNB + P.DOCS_IPYNB,
            "actions": [
                ["black", *P.EXAMPLE_IPYNB, *P.DOCS_IPYNB],
                ["nbqa", "ruff", "--fix", *P.EXAMPLE_IPYNB, *P.DOCS_IPYNB],
            ],
        },
        P.OK_NBQA_RUFF,
    )

    for dio_file in P.ALL_DIO + P.EXAMPLE_IPYNB + P.DOCS_IPYNB:
        name = f"dio:clean:{dio_file.relative_to(P.ROOT)}"
        dio_tasks += [f"lint:{name}"]
        yield {
            "name": name,
            "file_dep": [dio_file, *P.OK_PYSETUP.values()],
            "actions": [["jupyter", "ipydrawio", "clean", dio_file]],
        }

    yield P._ok(
        {
            "name": "dio:clean",
            "file_dep": [*P.ALL_DIO],
            "task_dep": dio_tasks,
            "actions": [["echo", "ok"]],
        },
        P.OK_DIOLINT,
    )

    yield P._ok(
        {
            "name": "all",
            "actions": [P._echo_ok("all ok")],
            "file_dep": [
                P.OK_BLACK,
                # P.OK_ESLINT,
                P.OK_RUFF,
                P.OK_PRETTIER,
                P.OK_BLACK_JUPYTER,
                P.OK_NBQA_RUFF,
            ],
        },
        P.OK_LINT,
    )

    yield P._ok(
        {
            "name": "robot:tidy",
            "file_dep": P.ALL_ROBOT,
            "actions": [["robotidy", *P.ALL_ROBOT]],
        },
        P.OK_ROBOTIDY,
    )

    yield P._ok(
        {
            "name": "robot:cop",
            "file_dep": [*P.ALL_ROBOT, P.OK_ROBOTIDY],
            "actions": [["robocop", *P.ALL_ROBOT]],
        },
        P.OK_ROBOCOP,
    )

    yield P._ok(
        {
            "name": "robot:dryrun",
            "file_dep": [*P.ALL_ROBOT, P.OK_ROBOCOP],
            "actions": [[*P.PYM, "scripts.atest", "--dryrun"]],
        },
        P.OK_ROBOT_DRYRUN,
    )


def task_build():
    """Build intermediates and release artifacts."""
    if P.TESTING_IN_CI:
        return

    yield from P.package_json_tasks(
        "build",
        "build:pre",
        P.OK_JS_BUILD_PRE,
        file_dep=[P.OK_SUBMODULES],
    )

    yield from P.package_json_tasks(
        "build",
        "build",
        P.OK_JS_BUILD,
        file_dep=[P.OK_JS_BUILD_PRE],
    )

    yield {
        "name": "readme:ipydrawio",
        "file_dep": [P.README],
        "targets": [P.IPD / "README.md"],
        "actions": [
            lambda: [
                (P.IPD / "README.md").write_text(P.README.read_text(), **P.ENC),
                None,
            ][-1],
        ],
    }

    for pkg, (file_dep, targets) in P.JS_PKG_PACK.items():
        yield {
            "name": f"pack:{pkg}",
            "file_dep": [*file_dep, *P.JS_TSBUILDINFO.values()],
            "actions": [
                CmdAction(
                    [P.NPM, "pack", "."],
                    cwd=str(targets[0].parent),
                    shell=False,
                ),
            ],
            "targets": targets,
        }
        pkg_data = P.JS_PKG_DATA[pkg]

        if "jupyterlab" not in pkg_data:
            continue

        out_dir = (
            P.JS_PKG_JSON[pkg].parent / pkg_data["jupyterlab"]["outputDir"]
        ).resolve()

        yield P._ok(
            {
                "name": f"ext:build:{pkg}",
                "actions": [
                    CmdAction(
                        [*P.LAB_EXT, "build", "."],
                        shell=False,
                        cwd=P.JS_PKG_JSON[pkg].parent,
                    ),
                ],
                "file_dep": targets,
                "targets": [out_dir / "package.json"],
            },
            P.OK_EXT_BUILD[pkg],
        )

    for py_pkg, py_setup in P.PY_SETUP.items():
        ext_deps = [
            (
                P.JS_PKG_JSON[ext].parent
                / P.JS_PKG_DATA[ext]["jupyterlab"]["outputDir"]
            ).resolve()
            / "package.json"
            for ext, mod in P.JS_LABEXT_PY_HOST.items()
            if mod == py_setup.parent.name
        ]

        file_dep = sorted(
            {
                *ext_deps,
                *P.PY_SRC[py_pkg],
                P.OK_SUBMODULES,
                py_setup,
                py_setup.parent / "MANIFEST.in",
                py_setup.parent / "README.md",
                py_setup.parent / "LICENSE.txt",
            },
        )

        if py_setup.parent == P.IPDE:
            file_dep += [P.IPDE_DIE2_YARN_LOCK]
        elif py_setup.parent == P.IPDW:
            for src, dest in P.IPDW_DEPS.items():
                file_dep += [dest]
                yield {
                    "name": f"copy:{py_pkg}:{src.name}",
                    "file_dep": [src],
                    "targets": [dest],
                    "actions": [(P._copy_one, [src, dest])],
                }

        yield {
            "name": f"sdist:{py_pkg}",
            "file_dep": file_dep,
            "actions": [
                CmdAction(
                    ["python", "setup.py", "sdist"],
                    shell=False,
                    cwd=str(py_setup.parent),
                ),
            ],
            "targets": [P.PY_SDIST[py_pkg]],
        }
        yield {
            "name": f"whl:{py_pkg}",
            "file_dep": file_dep,
            "actions": [
                CmdAction(
                    ["python", "setup.py", "bdist_wheel"],
                    shell=False,
                    cwd=str(py_setup.parent),
                ),
            ],
            "targets": [P.PY_WHEEL[py_pkg]],
        }

    def _make_hashfile():
        # mimic sha256sum CLI
        if P.SHA256SUMS.exists():
            P.SHA256SUMS.unlink()

        if not P.DIST.exists():
            P.DIST.mkdir(parents=True)

        [shutil.copy2(p, P.DIST / p.name) for p in P.HASH_DEPS]

        lines = []

        for p in P.HASH_DEPS:
            lines += ["  ".join([sha256(p.read_bytes()).hexdigest(), p.name])]

        output = "\n".join(lines)
        print(output)
        P.SHA256SUMS.write_text(output, **P.ENC)

    yield {
        "name": "hash",
        "file_dep": [*P.HASH_DEPS],
        "targets": [P.SHA256SUMS, *[P.DIST / d.name for d in P.HASH_DEPS]],
        "actions": [_make_hashfile],
    }


def task_conda_build():
    """Test building with conda-build."""
    yield {
        "name": "build",
        "file_dep": [
            P.RECIPE,
            P.CONDARC,
            *[P.DIST / p.name for p in P.PY_SDIST.values()],
        ],
        "actions": [
            [
                *P.CONDA_BUILD_ARGS,
                "--no-test",
                "--output-folder",
                P.CONDA_BLD,
                P.RECIPE.parent,
            ],
        ],
        "targets": [*P.CONDA_PKGS.values()],
    }


def task_conda_test():
    for name, pkg in P.CONDA_PKGS.items():
        yield P._ok(
            {
                "name": f"test:{name}",
                "file_dep": [pkg],
                "actions": [[*P.CONDA_BUILD_ARGS, "--test", pkg]],
            },
            P.OK_CONDA_TEST / f"{name}.ok",
        )


def task_serve():
    """Run processes "normally" (not watching sources)."""
    if P.TESTING_IN_CI:
        return

    def lab():
        proc = subprocess.Popen(P.CMD_LAB, stdin=subprocess.PIPE)

        try:
            proc.wait()
        except KeyboardInterrupt:
            print("attempting to stop lab, you may want to check your process monitor")
            proc.terminate()
            proc.communicate(b"y\n")

        proc.wait()

    yield {
        "name": "lab",
        "uptodate": [lambda: False],
        "file_dep": [*P.OK_SERVEREXT.values()],
        "actions": [PythonInteractiveAction(lab)],
    }

    yield {
        "name": "demo",
        "uptodate": [lambda: False],
        "file_dep": [P.DEMO_ARCHIVE],
        "actions": [(P._lite, [["doit"], ["--", "-s", "serve"]])],
    }


def _make_lab(watch=False):
    def _lab():
        if watch:
            print(">>> Starting typescript watcher...", flush=True)
            ts = subprocess.Popen(["jlpm", "run", "watch"], cwd=P.JS_META)

            ext_watchers = [
                subprocess.Popen([*P.LAB_EXT, "watch", "."], cwd=str(p.parent))
                for p in P.JS_PKG_JSON_LABEXT.values()
            ]

            print(">>> Waiting a bit to JupyterLab...", flush=True)
            time.sleep(3)
        print(">>> Starting JupyterLab...", flush=True)
        lab = subprocess.Popen(
            P.CMD_LAB,
            stdin=subprocess.PIPE,
        )

        try:
            print(">>> Waiting for JupyterLab to exit (Ctrl+C)...", flush=True)
            lab.wait()
        except KeyboardInterrupt:
            print(
                f""">>> {"Watch" if watch else "Run"} canceled by user!""",
                flush=True,
            )
        finally:
            print(">>> Stopping watchers...", flush=True)
            if watch:
                [x.terminate() for x in ext_watchers]
                ts.terminate()
            lab.terminate()
            lab.communicate(b"y\n")
            if watch:
                ts.wait()
                lab.wait()
                [x.wait() for x in ext_watchers]
                print(
                    ">>> Stopped watchers! maybe check process monitor...",
                    flush=True,
                )

        return True

    return _lab


def task_watch():
    """Watch things."""
    if P.TESTING_IN_CI:
        return

    yield {
        "name": "lab",
        "doc": "watch labextensions for changes, rebuilding",
        "uptodate": [lambda: False],
        "file_dep": [*P.OK_SERVEREXT.values(), P.OK_PIP_CHECK],
        "actions": [
            P.CMD_LIST_EXTENSIONS,
            PythonInteractiveAction(_make_lab(watch=True)),
        ],
    }

    yield {
        "name": "docs",
        "doc": "watch docs for changes, rebuilding",
        "uptodate": [lambda: False],
        "file_dep": [P.DOCS_BUILDINFO, P.OK_PIP_CHECK],
        "actions": [["sphinx-autobuild", *P.SPHINX_ARGS, "-j8", P.DOCS, P.DOCS_BUILD]],
    }


def task_demo():
    demo_dest = [*P.DEMO.glob("*.json")]
    demo_tasks = []
    final_dest = []

    yield {
        "name": "pyodide:packages",
        "doc": "fetch the pyodide packages.json",
        "uptodate": [doit.tools.config_changed(P.PYODIDE_URL)],
        "targets": [P.PYODIDE_PACKAGES],
        "actions": [P.fetch_pyodide_packages],
    }

    demo_tasks += ["demo:wheels"]

    yield {
        "name": "wheels",
        "doc": "fetch wheels",
        "file_dep": [P.PYODIDE_PACKAGES, P.DEMO_REQS],
        "actions": [P.fetch_wheels],
    }

    yield {
        "name": "extensions",
        "doc": "update jupyter_lite_config.json from the conda env",
        "file_dep": [P.ENV_BINDER, *P.PY_WHEEL.values()],
        "targets": [P.DEMO_CONFIG],
        "actions": [
            (
                P._sync_lite_config,
                [
                    P.ENV_BINDER,
                    P.DEMO_CONFIG,
                    P.FED_EXT_MARKER,
                    [P.PY_WHEEL[P.IPD.name]],
                    [P.PY_WHEEL[P.IPDW.name]],
                ],
            ),
        ],
    }

    for src, dest in P.ALL_DEMO_CONTENTS.items():
        name = f"stage:{src.name}"
        demo_dest += [dest]
        demo_tasks += [f"demo:{name}"]
        final_dest += [P.DEMO_BUILD / f"files/{src.name}"]
        yield {
            "name": name,
            "file_dep": [src],
            "targets": [dest],
            "actions": [(P._copy_one, [src, dest])],
        }

    assert demo_dest
    assert final_dest
    assert demo_tasks

    yield {
        "name": "archive",
        "task_dep": demo_tasks,
        "file_dep": [*demo_dest, *P.DEMO_WHEELS.glob(f"*{P.NOARCH_WHL}")],
        "targets": [P.DEMO_ARCHIVE, P.DEMO_HASHES, *final_dest, P.DEMO_CONTENTS_API],
        "actions": [(P._lite, [["build", "archive"], []])],
    }


def task_docs():
    """Build the docs."""
    if P.TESTING_IN_CI:
        return

    if shutil.which("convert"):
        yield {
            "name": "favicon",
            "doc": "regenerate the favicon",
            "file_dep": [P.DOCS_FAVICON_SVG],
            "actions": [
                [
                    "convert",
                    "-density",
                    "256x256",
                    "-background",
                    "transparent",
                    P.DOCS_FAVICON_SVG,
                    "-define",
                    "icon:auto-resize",
                    "-colors",
                    "256",
                    P.DOCS_FAVICON_ICO,
                ],
            ],
            "targets": [P.DOCS_FAVICON_ICO],
        }

    yield {
        "name": "typedoc:ensure",
        "file_dep": [*P.JS_PKG_JSON.values()],
        "actions": [P.typedoc_conf],
        "targets": [P.TYPEDOC_JSON, P.TSCONFIG_TYPEDOC],
    }

    yield {
        "name": "typedoc:build",
        "doc": "build the TS API documentation with typedoc",
        "file_dep": [*P.JS_TSBUILDINFO.values(), *P.TYPEDOC_CONF, P.YARN_INTEGRITY],
        "actions": [["jlpm", "typedoc", "--options", P.TYPEDOC_JSON]],
        "targets": [P.DOCS_RAW_TYPEDOC_README],
    }

    yield {
        "name": "typedoc:mystify",
        "doc": "transform raw typedoc into myst markdown",
        "file_dep": [P.DOCS_RAW_TYPEDOC_README],
        "targets": [P.DOCS_TS_MYST_INDEX, *P.DOCS_TS_MODULES],
        "actions": [
            P.mystify,
            [
                "jlpm",
                "prettier",
                "--list-different",
                "--write",
                P.DOCS_TS_MYST_INDEX.parent,
            ],
        ],
    }

    sphinx_deps = [
        *P.ALL_DOCS_STATIC,
        *P.DOCS_SRC,
        P.DEMO_ARCHIVE,
        P.DEMO_HASHES,
        P.DOCS_CONF,
        P.DOCS_FAVICON_ICO,
        P.OK_PIP_CHECK,
    ]
    sphinx_task_deps = []

    yield {
        "name": "sphinx",
        "doc": "build the documentation site with sphinx",
        "file_dep": sphinx_deps,
        "task_dep": sphinx_task_deps,
        "actions": [
            ["sphinx-build", *P.SPHINX_ARGS, "-b", "html", P.DOCS, P.DOCS_BUILD],
        ],
        "targets": [P.DOCS_BUILDINFO],
    }


@doit.create_after("docs")
def task_check():
    """Check built artifacts."""
    file_dep = [*P.DOCS_BUILD.rglob("*.html")]
    yield P._ok(
        {
            "name": "links",
            "file_dep": [*file_dep, P.DOCS_BUILDINFO],
            "actions": [
                [
                    "pytest-check-links",
                    "--check-anchors",
                    "--check-links-ignore",
                    "http://",
                    "--check-links-ignore",
                    "https://",
                    *[p for p in file_dep if p.name not in ["schema.html"]],
                ],
            ],
        },
        P.OK_LINK_CHECK,
    )


def task_provision():
    """Ensure the ipydrawio-export server has been provisioned with npm (ick)."""
    return P._ok(
        {
            "file_dep": [*P.OK_SERVEREXT.values()],
            "actions": [
                ["jupyter", "ipydrawio-export", "--version"],
                ["jupyter", "ipydrawio-export", "provision"],
            ],
        },
        P.OK_PROVISION,
    )


def _pytest(setup_py, pycov_args, pytest_args):
    return CmdAction(
        [
            *P.PYM,
            "coverage",
            "run",
            *pycov_args,
            "-m",
            "pytest",
            *P.PYTEST_ARGS,
            *pytest_args,
        ],
        shell=False,
        cwd=str(setup_py.parent),
        env=dict(
            COVERAGE_PROCESS_START="1",
            **os.environ,
        ),
    )


def _pycov_combine(setup_py):
    return CmdAction(
        [*P.PYM, "coverage", "combine"],
        shell=False,
        cwd=str(setup_py.parent),
    )


def _pycov_report(setup_py):
    return CmdAction(
        [*P.PYM, "coverage", "report", "--skip-covered", "--show-missing"],
        shell=False,
        cwd=str(setup_py.parent),
    )


def _pycov_html(setup_py, *pycov_html_args):
    return CmdAction(
        [*P.PYM, "coverage", "html", *pycov_html_args],
        shell=False,
        cwd=str(setup_py.parent),
    )


def task_test():
    """Run tests."""
    if not P.TESTING_IN_CI:
        yield P._ok(
            {
                "name": "integrity",
                "file_dep": [
                    *P.OK_SERVEREXT.values(),
                    *P.PY_SDIST.values(),
                    *P.PY_WHEEL.values(),
                    *P.IPDW_DEPS.values(),
                    *P.ALL_SETUP_CFG,
                    P.DEMO_CONFIG,
                    P.ENV_BINDER,
                    P.OK_LINT,
                    P.RECIPE,
                    P.SCRIPTS / "integrity.py",
                ],
                "actions": [
                    ["python", "-m", "pytest", "--pyargs", "scripts.integrity", "-vv"],
                ],
            },
            P.OK_INTEGRITY,
        )

    for pkg, setup in P.PY_SETUP.items():
        html = P.BUILD / f"pytest/{pkg}/test.html"
        htmlcov = P.BUILD / f"pytest/{pkg}/htmlcov"
        pytest_args = [
            "-vv",
            "--tb=long",
            f"--html={html}",
            "--self-contained-html",
            "--script-launch-mode=subprocess",
            "--cov-context=test",
        ]
        pycov_args = []
        pycov_html_args = [f"--directory={htmlcov.parent}"]

        if pkg == P.IPD.name:
            pytest_args += ["-n", "auto"]

        yield P._ok(
            {
                "name": f"pytest:{pkg}",
                "uptodate": [config_changed({"PYTEST_ARGS": P.PYTEST_ARGS})],
                "file_dep": [
                    *P.PY_SRC[pkg],
                    P.PY_SETUP_CFG[pkg],
                    *P.PY_TEST_DEP.get(pkg, []),
                    P.OK_PROVISION,
                    P.OK_PIP_CHECK,
                ],
                "actions": [
                    (P.delete_some, [html]),
                    _pytest(setup, pycov_args, pytest_args),
                    _pycov_combine(setup),
                    _pycov_html(setup, *pycov_html_args),
                    _pycov_report(setup),
                ],
                "targets": [html],
            },
            P.OK_PYTEST[pkg],
        )

    file_dep = [
        *P.ALL_ROBOT,
        P.OK_PROVISION,
        *sum(P.PY_SRC.values(), []),
        *sum(P.JS_TSSRC.values(), []),
        P.SCRIPTS / "atest.py",
    ]

    if not P.TESTING_IN_CI:
        file_dep += [
            P.OK_ROBOT_DRYRUN,
            P.DEMO_HASHES,
            *P.OK_SERVEREXT.values(),
        ]

        demo_files = [P.DEMO_FILES / p.name for p in P.ALL_DEMO_CONTENTS]

        for tmpl in P.ATEST_TEMPLATES:
            dest = tmpl.parent / tmpl.name.replace(".j2", "")
            yield {
                "name": f"template:{tmpl.relative_to(P.ATEST)}",
                "file_dep": [tmpl, *demo_files],
                "targets": [dest],
                "actions": [
                    (P.template_one, [tmpl, dest]),
                    ["robotidy", dest],
                ],
            }

    yield P._ok(
        {
            "name": "robot",
            "uptodate": [
                config_changed(
                    {"ATEST_ARGS": P.ATEST_ARGS, "ATEST_ATTEMPT": P.ATEST_ATTEMPT},
                ),
            ],
            "file_dep": file_dep,
            "actions": [["python", "-m", "scripts.atest"]],
        },
        P.OK_ATEST,
    )
