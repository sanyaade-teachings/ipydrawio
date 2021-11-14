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
Documentation     A work-in-progress set of keywords for RetroLab
Library           SeleniumLibrary
Resource          ../_Keywords.robot

*** Keywords ***
Setup Server and Retro Browser
    Setup Server and Browser
    Set Screenshot Directory    ${OUTPUT DIR}${/}retro
    Open Retro Tree

Open Retro Tree
    Go To    ${URL}retro/tree
    Wait Until Page Contains Element    css:#main
    Sleep    1s
