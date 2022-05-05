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
Documentation       Test some diagrams in lite

Resource            ../_Keywords.robot
Resource            ./_Keywords.robot
Library             OperatingSystem

Suite Setup         Set Screenshot Directory    ${OUTPUT DIR}${/}lite${/}documents

Force Tags          component:document


*** Test Cases ***
Poster Dio Svg
    [Documentation]    Does the Poster.dio.svg example document work?
    Example Document Should Load    Poster.dio.svg

Roadmap Dio Svg
    [Documentation]    Does the ROADMAP.dio.svg example document work?
    Example Document Should Load    ROADMAP.dio.svg

Affinity Dio Svg
    [Documentation]    Does the affinity.dio.svg example document work?
    Example Document Should Load    affinity.dio.svg

Comp Dio Svg
    [Documentation]    Does the comp.dio.svg example document work?
    Example Document Should Load    comp.dio.svg

Deployment Dio Svg
    [Documentation]    Does the deployment.dio.svg example document work?
    Example Document Should Load    deployment.dio.svg

Mermaid Dio Svg
    [Documentation]    Does the mermaid.dio.svg example document work?
    Example Document Should Load    mermaid.dio.svg

Mindmap Dio Svg
    [Documentation]    Does the mindmap.dio.svg example document work?
    Example Document Should Load    mindmap.dio.svg

Wireframe Dio Svg
    [Documentation]    Does the wireframe.dio.svg example document work?
    Example Document Should Load    wireframe.dio.svg

What-Can-You-Draw Dio Svg
    [Documentation]    Does the what-can-you-draw.dio.svg example document work?
    Example Document Should Load    what-can-you-draw.dio.svg


*** Keywords ***
Example Document Should Load
    [Documentation]    Does one example document work?
    [Arguments]    ${file}
    Try to Close All Tabs
    Ensure File Browser is Open
    Double Click Element    css:[title*\="${file}"]
    Unselect Frame
    Wait Until Element is Visible    ${CSS DIO IFRAME}    timeout=20s
    Capture Page Screenshot    00-${file}-loaded.png
