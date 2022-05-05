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
Documentation       Common behaviors for CodeMirror instances


*** Keywords ***
Set CodeMirror Value
    [Documentation]    Set the value in the CodeMirror attached to the element
    ...    that matches a ``css`` selector to be the given ``text``.
    [Arguments]    ${css}    ${code}
    Select All CodeMirror Text    ${css}
    Replace CodeMirror Selection    ${css}    ${code}

Select All CodeMirror Text
    [Documentation]    Select all of the text in the CodeMirror attached to the element
    ...    matched by a ``css`` selector.
    [Arguments]    ${css}
    Execute CodeMirror Command    ${css}    selectAll

Execute CodeMirror Command
    [Documentation]    Run a CodeMirror [https://codemirror.net/doc/manual.html#commands:command]
    ...    ``cmd`` for the editor attached to element that matches a ``css`` selector
    [Arguments]    ${css}    ${cmd}
    Call CodeMirror Method    ${css}    execCommand("${cmd}")

Replace CodeMirror Selection
    [Documentation]    Replace all of the text in the CodeMirror attached to the element
    ...    that matches a ``css`` selector with the given ``text``.
    [Arguments]    ${css}    ${code}
    Call CodeMirror Method    ${css}    replaceSelection(`${code}`)

Call CodeMirror Method
    [Documentation]    Construct and a method call against in the CodeMirror attached to the element
    ...    that matches a ``css`` selector with the given ``js`` code.
    [Arguments]    ${css}    ${js}
    Execute JavaScript    document.querySelector(`${css}`).CodeMirror.${js}
