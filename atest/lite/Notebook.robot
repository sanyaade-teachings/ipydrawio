*** Comments ***
# Copyright 2022 ipydrawio contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


*** Settings ***
Documentation       Test some notebooks in lite

Resource            ../_Keywords.robot
Resource            ./_Keywords.robot
Library             OperatingSystem

Suite Setup         Set Screenshot Directory    ${OUTPUT DIR}${/}lite${/}notebooks

Force Tags          component:notebook


*** Variables ***
${PYOLITE BUSY}     Pyolite | Busy


*** Test Cases ***
Diagram Document
    [Documentation]    Does the Diagram Document example notebook work?
    Notebook Should Run Without Error    Diagram Document.ipynb

Diagram Rich Display
    [Documentation]    Does the Diagram Rich Display example notebook work?
    Notebook Should Run Without Error    Diagram Rich Display.ipynb

Diagram Widget
    [Documentation]    Does the Diagram Widget example notebook work?
    Notebook Should Run Without Error    Diagram Widget.ipynb

Roadmap
    [Documentation]    Does the ROADMAP example notebook work?
    Notebook Should Run Without Error    ROADMAP.ipynb


*** Keywords ***
Notebook Should Run Without Error
    [Documentation]    Does one example notebook work?
    [Arguments]    ${file}
    Try to Close All Tabs
    ${stem} =    Set Variable    ${file.lower().replace(" ", "-").split(".")[0]}
    Ensure File Browser is Open
    Double Click Element    css:[title*\="${file}"]
    Lab Command    Show Log Console
    Lab Command    Run All Cells
    Capture Page Screenshot    ${stem}-00-loaded.png
    Wait Until Page Does Not Contain    ${PYOLITE BUSY}    timeout=120s
    Page Should Not Contain    Widget Model Not Found
    Page Should Not Contain    Traceback
    Capture Page Screenshot    ${stem}-01-run.png
