"""update the vendored drawio."""

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

import pprint
import shutil
from fnmatch import fnmatch

from . import ALL_DIO, PACKAGES, ROOT

IGNORE = ROOT / ".npmignore"
IGNORED = {
    glob.strip(): 0
    for glob in IGNORE.read_text().strip().splitlines()
    if glob.startswith("dio/")
}

HEADER = """
/**
    All drawio files that should be included in @deathbeds/{pkg}

    This file generated from https://github.com/jgraph/drawio
*/
"""

TMPL = """
import '!!file-loader?name=[path][name].[ext]&context=.!../dio{}';
"""


def is_ignored(path, root):
    rel = str(path.relative_to(root))
    print("... considering", rel, flush=True)
    for ignore in IGNORED:
        if fnmatch(rel, ignore):
            IGNORED[ignore] += 1
            print("   ... ignored!")
            return True
    return False


def update_one_static(pkg, dio, static):
    print(f"... updating {static}", flush=True)
    lines = []

    all_paths = sorted(dio.rglob("*"))

    for path in all_paths:
        if is_ignored(path, dio.parent):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            continue
        if path.is_dir():
            continue
        if not path.exists():
            continue
        lines += [
            TMPL.format(str(path.as_posix()).replace(str(dio.as_posix()), "")).strip(),
        ]

    if not lines:
        raise ValueError

    static.write_text("\n".join([HEADER.format(pkg=pkg), *lines]))
    print(
        f"    ... {static.relative_to(PACKAGES)} wrote {len(lines)} lines",
        flush=True,
    )


def update_static():
    for pkg, dio in ALL_DIO.items():
        static = dio.parent / "lib/_static.js"
        if static.exists():
            static.unlink()
        update_one_static(pkg, dio, static)
    print("ignored\n", pprint.pformat(IGNORED))


if __name__ == "__main__":
    update_static()
