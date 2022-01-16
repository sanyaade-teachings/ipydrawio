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
Documentation     Does the Jupyter Widget work?
Resource          ../_Keywords.robot
Resource          ../_Notebook.robot
Force Tags        component:widget
Library           OperatingSystem

*** Test Cases ***
Diagram Widget
    [Documentation]    does the Jupyter Widget work?
    Create Diagram Widget    smoke
    Capture Page Screenshot    00-on-page.png
    Edit the Widget
    Capture Page Screenshot    01-edited.png
    Update The Diagram Widget Value    ${FIXTURES}${/}test.dio
    Diagram Should Contain    TEST123
    Capture Page Screenshot    02-updated.png
    Change Paper Size    a3
    Should Be True In Cell    diagram.page_format["width"] == 1169
    Capture Page Screenshot    03-resized.png
    Change Paper Size    letter
    Should Be True In Cell    diagram.page_format["width"] == 850
    Capture Page Screenshot    04-resized-again.png

Many Shapes
    [Documentation]    does the viewport change unpredictably with many shapes?
    [Tags]    gh:85
    Create Diagram Widget    eleven    ${TRUE}
    Edit the Widget
    Duplicate Shape    10
    Select All From List    css:select[multiple]
    Capture Page Screenshot    01-eleven.png

*** Keywords ***
Create Diagram Widget
    [Arguments]    ${label}    ${add multiple}=${FALSE}
    Set Screenshot Directory    ${OUTPUT DIR}${/}screenshots${/}widget${/}${label}
    Launch Untitled Notebook
    Add and Run JupyterLab Code Cell    import ipywidgets as W, traitlets as T; from ipydrawio import Diagram
    Add and Run JupyterLab Code Cell    diagram = Diagram(layout\=dict(min_height\="60vh"));
    IF    ${add multiple}
        Create Linked SelectMultiple
    END
    Add and Run JupyterLab Code Cell    diagram
    Wait Until Page Contains Element    ${CSS DIO READY} iframe

Create Linked SelectMultiple
    Add and Run JupyterLab Code Cell    opts = W.SelectMultiple()
    Add and Run JupyterLab Code Cell    T.dlink((diagram, "cell_ids"), (opts, "options"));
    Add and Run JupyterLab Code Cell    T.link((opts, "value"), (diagram, "selected_cells")); opts

Should Be True In Cell
    [Arguments]    ${code}
    Add and Run JupyterLab Code Cell    assert (${code})
    Wait Until JupyterLab Kernel Is Idle
    Page Should Not Contain Element    css:[data-mime-type\="${MIME STDERR}"]

Duplicate Shape
    [Arguments]    ${duplicates}
    Select Frame    ${CSS DIO IFRAME}
    Click Element At Coordinates    ${CSS DIO BG}    100    100
    FOR    ${i}    IN RANGE    ${duplicates}
        Sleep    0.1s
        ${els} =    Get WebElements    css:rect[width\="120"]
        Click Element    ${els[-1]}
        Press Keys    css:body    ${ACCEL}+D
    END
    [Teardown]    Unselect Frame

Unselect Shape
    Select Frame    ${CSS DIO IFRAME}
    Click Element At Coordinates    ${CSS DIO BG}    200    200
    [Teardown]    Unselect Frame

Add A Shape at Offset
    [Arguments]    ${x}    ${y}
    Double Click Element    ${CSS DIO BG}
    ${a shape} =    Set Variable    ${CSS DIO SHAPE POPUP SHAPE}:nth-child(2)
    Wait Until Element Is Visible    ${a shape}
    Click Element    ${a shape}
    Drag And Drop By Offset    css:rect[width\="120"]    ${x}    ${y}

Edit the Widget
    Select Frame    ${CSS DIO IFRAME}
    Double Click Element    ${CSS DIO BG}
    ${a shape} =    Set Variable    ${CSS DIO SHAPE POPUP SHAPE}:nth-child(2)
    Wait Until Element Is Visible    ${a shape}
    Click Element    ${a shape}
    Sleep    0.5s
    [Teardown]    Unselect Frame

Diagram Should Contain
    [Arguments]    ${text}
    Select Frame    ${CSS DIO IFRAME}
    Wait Until Page Contains    ${text}
    [Teardown]    Unselect Frame

Update The Diagram Widget Value
    [Arguments]    ${path}
    ${xml} =    Get File    ${path}
    Add and Run JupyterLab Code Cell    diagram.source.value = '''${xml.strip()}'''
    Press Keys    None    ESC
    Press Keys    None    UP

Change Paper Size
    [Arguments]    ${size}=letter
    Scroll Element Into View    ${CSS DIO IFRAME}
    Select Frame    ${CSS DIO IFRAME}
    Maybe Open Format Pane
    ${el} =    Get WebElement    xpath:${XP DIO PAGE SIZE}
    Select From List By Value    ${el}    ${size}
    [Teardown]    Unselect Frame

Maybe Open Format Pane
    ${els} =    Get WebElements    xpath:${XP DIO FORMAT PANE VISIBLE}
    Run Keyword If    not ${els.__len__()}    Click Element    xpath:${XP DIO FORMAT TOGGLE}
    Wait Until Page Contains Element    xpath:${XP DIO FORMAT PANE VISIBLE}

Measure Paper
    ${size} =    Get Element Size    css:.geBackgroundPage
    [Return]    ${size}
