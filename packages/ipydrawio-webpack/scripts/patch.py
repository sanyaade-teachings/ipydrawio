""" patch drawio sources for embedding in JupyterLab"""

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


import shutil
import sys

from . import DIO, DRAWIO, EXTERNAL, PACKAGES

IPDM_REL = "../../../ipydrawio-mathjax/static/dio"

PATCHES = {
    "js/app.min.js": [
        {
            "name": "add global ref so we can get at the App at runtime",
            "before": "new App(new Editor",
            "after": "window.IPYDRAWIO_APP = new App(new Editor",
        },
        {
            "name": "patch cors check for data URI",
            "before": "this.editor.isCorsEnabledForUrl(y)||(m=",
            "after": "(y.match(/^data:/) || this.editor.isCorsEnabledForUrl(y))||(m=",
        },
        {
            "name": "get mathjax from the ipydrawio-mathjax",
            "before": "window.DRAW_MATH_URL=",
            "after": f'window.DRAW_MATH_URL="{IPDM_REL}/math/es5";',
        },
    ]
}


def copy():
    if DIO.exists():
        print(f"... cleaning {DIO.relative_to(PACKAGES)}", flush=True)
        shutil.rmtree(DIO)

    print(
        f"... copying {DRAWIO.relative_to(PACKAGES)} --> {DIO.relative_to(PACKAGES)}",
        flush=True,
    )
    shutil.copytree(DRAWIO, DIO)

    for src, dest in EXTERNAL.items():
        rel_src = src.relative_to(PACKAGES)
        rel_dest = dest.relative_to(PACKAGES)
        if dest.exists():
            print(f"    ... cleaning {rel_dest}", flush=True)
            shutil.rmtree(dest)
        print(f"    ... moving {rel_src} --> {rel_dest}", flush=True)
        if not src.exists():
            print(f"    !!! {rel_src} is missing", flush=True)
            return 1
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dest)

    return 0


def patch():
    for path, patches in PATCHES.items():
        src_path = DRAWIO / path
        dest_path = DIO / path
        txt = src_path.read_text(encoding="utf-8")

        for patch in patches:
            print("  ", patch["name"])
            if patch["before"] not in txt:
                print("Couldn't find", patch["before"])
            elif patch["after"] not in txt:
                print("   ...patching")
                txt = txt.replace(patch["before"], patch["after"])
            else:
                raise ValueError(f"{path} didn't contain {patch}")

        dest_path.write_text(txt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(copy() + patch())
