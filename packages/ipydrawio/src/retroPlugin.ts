/*
  Copyright 2021 ipydrawio contributors

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

import { PLUGIN_ID, CommandIds, DEBUG } from '.';
import { IDiagramManager } from './tokens';
import { PageConfig } from '@jupyterlab/coreutils';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { DiagramDocument } from '.';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';

import { JupyterLab, JupyterFrontEndPlugin } from '@jupyterlab/application';

import { CommandToolbarButton } from '@jupyterlab/apputils';

/**
 * The editor tracker extension.
 */
const retroPlugin: JupyterFrontEndPlugin<void> = {
  activate,
  id: `${PLUGIN_ID}-retro`,
  requires: [IDiagramManager],
  optional: [IFileBrowserFactory],
  autoStart: true,
};

function activate(
  app: JupyterLab,
  manager: IDiagramManager,
  fileBrowser: IFileBrowserFactory
) {
  const retroPage = PageConfig.getOption('retroPage');
  const { commands } = app;

  DEBUG && console.warn('retro page is', retroPage);

  if (retroPage == 'tree') {
    const newDiagram = new CommandToolbarButton({
      commands,
      id: CommandIds.createNew,
    });
    fileBrowser.defaultBrowser.toolbar.insertItem(2, 'new-diagram', newDiagram);
  } else if (retroPage === 'edit') {
    app.shell.currentChanged.connect(async (changed) => {
      const { currentWidget } = app.shell;
      if (!currentWidget || currentWidget instanceof DiagramDocument) {
        return;
      }
      const context = (currentWidget as any)
        .context as DocumentRegistry.Context;
      if (!context) {
        return;
      }
      await context.ready;
      if (!context.contentsModel) {
        return;
      }
      const format = manager.formatForModel(context.contentsModel);
      if (!format || !format.isDefault) {
        return;
      }
      const factory = app.docRegistry.getWidgetFactory(format.factoryName);
      if (!factory) {
        return;
      }
      const favicon = document.querySelector(
        'link[rel="icon"], link.favicon'
      ) as HTMLLinkElement;
      favicon.href = `data:image/svg+xml;utf8,${encodeURIComponent(
        format.icon.svgstr
      )}`;
      favicon.type = 'image/svg+xml';
      app.shell.addClass('jp-IPyDiagram-main');

      currentWidget.dispose();

      await app.commands.execute('docmanager:open', {
        path: context.path,
        factory: factory.name,
        options: { ref: '_noref' },
      });
    });
  }
}

export default retroPlugin;
