# Copyright 2021 ipydrawio contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#                 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

*** Settings ***
Documentation     Do the tutorials work?
Resource          ../_Keywords.robot
Library           OperatingSystem
Force Tags        component:tutorials
Suite Setup       Set Screenshot Directory    ${OUTPUT DIR}${/}screenshots${/}tutorials

*** Test Cases ***
Custom Library URL Hack
    [Documentation]    Does using a custom library work?
    [Tags]    component:widget
    Copy File    ${CLIB TUTORIAL}    ${HOME}${/}clib.ipynb
    Wait Until Keyword Succeeds    5x    5s    Open clib.ipynb in ${MENU NOTEBOOK}
    Lab Command    Run All Cells
    Wait Until Page Does Not Contain    [*]
    Click Element    css:.jp-Cell:last-child
    Wait Until Keyword Succeeds    5x    5s    Wait for a Diagram to be Ready
    Current Frame Should Contain    my+library
    Current Frame Should Contain    banana
    [Teardown]    Tear Down Custom Library Tutorial

*** Keywords ***
Tear Down Custom Library Tutorial
    Unselect Frame
    Remove File    ${HOME}${/}clib.ipynb
