/*
  Copyright 2021 ipydrawio contributors
  Copyright 2020 jupyterlab-drawio contributors

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

import { Throttler } from '@lumino/polling';
import { JSONExt } from '@lumino/coreutils';

import {
  unpack_models as deserialize,
  WidgetModel,
  WidgetView,
} from '@jupyter-widgets/base';
import { BoxModel, BoxView } from '@jupyter-widgets/controls';

import { DRAWIO_URL } from '@deathbeds/ipydrawio-webpack';

import { Diagram } from './editor';

import {
  DEBUG,
  IDiagramManager,
  IMXCell,
  IMXEvent,
  IMXEventSource,
  MX_APP_MODEL_EVENTS,
  MX_EDITOR_EVENTS,
  MX_GRAPH_EVENTS,
  MX_GRAPH_MODEL_EVENTS,
  MX_GRAPH_PAN_EVENTS,
  MX_GRAPH_SELECT_EVENTS,
  MX_GRAPH_VIEW_EVENTS,
  NS,
  VERSION,
} from './tokens';

import '../style/widget.css';
import { IMXApp, IMXGraph, IMXGraphModel, IMXPage } from '.';

/**
 * An empty drawio diagaram.
 */
const A_SHORT_DRAWIO = `<mxfile version="13.3.6">
<diagram id="x" name="Page-1">
    <mxGraphModel dx="1450" dy="467" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
    <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
    </root>
    </mxGraphModel>
</diagram>
</mxfile>
`;

/**
 * Some sensible default URL values
 *
 * Note that `stealth` must be enabled to use URL-encoded shape libraries.
 */
const DEFAULT_URL_PARAMS = {
  gapi: 0,
  gl: 0,
  noExitBtn: 1,
  noSaveBtn: 1,
  od: 0,
  stealth: 1,
  tr: 0,
  ui: 'min',
  format: 0,
  p: 'ex;tips;svgdata;sql;anim;trees;replay;anon;flow;webcola;tags',
};

/**
 * Some sensible default config values.
 */
const DEFAULT_DRAWIO_CONFIG = {
  compressXml: false,
  showStartScreen: false,
  override: true,
};

/**
 * A model of the underlying XML for a drawio diagram
 */
export class XMLModel extends WidgetModel {
  static model_name = 'XMLModel';
  static model_module = NS;
  static model_module_version = VERSION;

  static view_name = 'XMLView';
  static view_module = NS;
  static view_module_version = VERSION;

  /**
   * The default tratlet values for an XML source
   */
  defaults() {
    return {
      ...super.defaults(),
      _model_name: XMLModel.model_name,
      _model_module: NS,
      _model_module_version: VERSION,
      _view_name: XMLModel.view_name,
      _view_module: NS,
      _view_module_version: VERSION,
      value: A_SHORT_DRAWIO,
    };
  }
}

/**
 * A dummy view for an XMLModel
 */
export class XMLView extends WidgetView {
  model: XMLModel;
}

/**
 * A model of a Diagram
 */
export class DiagramModel extends BoxModel {
  static model_name = 'DiagramModel';
  static model_module = NS;
  static model_module_version = VERSION;

  static view_name = 'DiagramView';
  static view_module = NS;
  static view_module_version = VERSION;

  static serializers = { ...BoxModel.serializers, source: { deserialize } };

  /**
   * Default traitlet values for a diagram
   */
  defaults() {
    return {
      ...super.defaults(),
      _model_name: DiagramModel.model_name,
      _model_module: NS,
      _model_module_version: VERSION,
      _view_name: DiagramModel.view_name,
      _view_module: NS,
      _view_module_version: VERSION,
      scroll_x: 0.0,
      scroll_y: 0.0,
      zoom: 1.0,
      page_ids: [],
      selected_page: 0,
      selected_cells: [],
      cell_ids: [],
      grid_enabled: true,
      grid_color: '#66666666',
      grid_size: 10,
      url_params: DEFAULT_URL_PARAMS,
      config: DEFAULT_DRAWIO_CONFIG,
      page_format: { x: 0, y: 0, width: 850, height: 1100 },
    };
  }
}

/**
 * A renderer for a Diagram.
 */
export class DiagramView extends BoxView {
  static diagrmManager: IDiagramManager;

  model: DiagramModel;

  protected diagram: Diagram;
  private _displayInterval: number;

  /**
   * Render the diagram, and schedule re-rerendering for when actually displayed.
   */
  render() {
    super.render();
    this.pWidget.addClass('jp-IPyDiagram');
    this._displayInterval = setInterval(this.waitForDisplayed, 50);
  }

  /**
   * A low-tech way to wait until we are quite sure the diagram is displayed.
   */
  protected waitForDisplayed() {
    if (!this.pWidget.isVisible) {
      return;
    }
    clearInterval(this._displayInterval);
    this.initDiagram();
    this.pWidget.addWidget(this.diagram);
    this.diagram.onContentChanged();
    this.diagram.onAfterShow();
    this.model.on('change:source', this.onModelSourceChange, this);
    this.onModelSourceChange();
  }

  /**
   * The drawio App
   */
  get app(): IMXApp {
    return this.diagram.app;
  }

  /**
   * The drawio Graph
   */
  get graph(): IMXGraph {
    return this.diagram.app.editor.graph;
  }

  /**
   * The drawio Graph Model
   */
  get graphModel(): IMXGraphModel {
    return this.diagram.app.editor.graph.model;
  }

  /**
   * Handle the XML source changing in the kernel, subscribe to its value changing.
   */
  protected onModelSourceChange() {
    const oldSource = (this.model.changed as any).source as XMLModel;
    if (oldSource != null) {
      oldSource.off('change:value', this.onSourceValue, this);
    }
    const source = this.model.get('source');
    if (source != null) {
      source.on('change:value', this.onSourceValue, this);
    }
  }

  /**
   * Handle the XML source's value changing
   */
  protected onSourceValue() {
    DEBUG && console.warn('change:value');
    this.diagram.onContentChanged();
  }

  /**
   * Initialize the actual Diagram renderer.
   */
  protected initDiagram() {
    DEBUG && console.warn('creating diagram widget');
    // TODO: consider hoisting this to the source
    const format = DiagramView.diagrmManager.formatForModel({
      path: 'widget.dio',
    });
    this.diagram = new Diagram({
      adapter: {
        saveNeedsExport: () => false,
        drawioUrl: () => DRAWIO_URL,
        drawioConfig: () => this.model.get('config'),
        urlParams: () => this.model.get('url_params'),
        format: () => format,
        toXML: () => this.xml(),
        fromXML: (xml) => {
          if ((this.xml() || '').trim() === (xml || '').trim()) {
            return;
          }
          this.xml(xml);
        },
      },
    });
    this.diagram.appChanged.connect(this.onAppChanged, this);
  }

  /**
   * Set or get the source.
   */
  protected xml(value?: string) {
    const source: XMLModel = this.model.get('source');

    if (value == null) {
      return source?.get('value');
    }

    if (source != null) {
      source.set({ value });
      source.save_changes(this.callbacks());
    }

    return;
  }

  /**
   * Handle the drawio app actually being ready, connecting events, etc.
   */
  protected onAppChanged() {
    const { app } = this.diagram;

    if (!app) {
      return;
    }

    DEBUG && console.warn('installing handlers on', app);

    const { editor } = app;
    const { graph } = editor;
    const { view, model, panningHandler, selectionModel } = graph;

    const emitters = [
      { src: app, evts: MX_APP_MODEL_EVENTS },
      { src: editor, evts: MX_EDITOR_EVENTS },
      { src: graph, evts: MX_GRAPH_EVENTS },
      { src: view, evts: MX_GRAPH_VIEW_EVENTS },
      { src: model, evts: MX_GRAPH_MODEL_EVENTS },
      { src: panningHandler, evts: MX_GRAPH_PAN_EVENTS },
      { src: selectionModel, evts: MX_GRAPH_SELECT_EVENTS },
    ];

    // mxgraph model, not widget model
    for (const { src, evts } of emitters) {
      for (const evt of evts) {
        (src as any).addListener(evt, this.onDrawioEvent);
      }
    }

    // wire up listeners from opposite direction
    // edge: 'trailing',
    const bounceOpts: Throttler.IOptions = { limit: 10 };
    [
      { evt: 'change:zoom', fn: this.onModelZoom },
      { evt: 'change:scroll_x change:scroll_y', fn: this.onModelScroll },
      { evt: 'change:page_format', fn: this.onModelPageFormat },
      { evt: 'change:current_page', fn: this.onModelPageSelected },
      { evt: 'change:grid_enabled', fn: this.onModelGridEnabled },
      { evt: 'change:grid_size', fn: this.onModelGridSize },
      { evt: 'change:grid_color', fn: this.onModelGridColor },
      { evt: 'change:selected_cells', fn: this.onModelSelectedCells },
    ].forEach(({ evt, fn }) => {
      const throttle = new Throttler(fn, bounceOpts);
      this.model.on(evt, () => throttle.invoke(), this);
    });

    this.model.set('cell_ids', this.getCellIds());
    this.touch();
  }

  /**
   * Handle a zoom change from the kernel
   */
  protected onModelZoom = () => {
    const { view } = this.graph;
    const wz = this.model.get('zoom');
    if (view.getScale() !== wz) {
      view.setScale(wz);
    }
  };

  /**
   * Handle a scroll change from the kernel
   */
  protected onModelScroll = () => {
    const { view } = this.graph;
    const wx = this.model.get('scroll_x');
    const wy = this.model.get('scroll_y');
    const tx = view.getTranslate();
    if (tx.x !== wx || tx.y !== wy) {
      view.setTranslate(wx, wy);
    }
  };

  /**
   * Handle a page format change from the kernel
   */
  protected onModelPageFormat = () => {
    const { app, model, graph } = this;
    const newFmt = model.get('page_format');
    const oldFmt = graph.pageFormat as any;
    if (!JSONExt.deepEqual(newFmt, oldFmt)) {
      DEBUG && console.warn('pageFormat', newFmt);
      app.setPageFormat({ ...newFmt });
    }
  };

  /**
   * Handle a page selection change from the kernel
   */
  protected onModelPageSelected = () => {
    const { app } = this;
    app.selectPage(app.pages[this.model.get('current_page')]);
  };

  /**
   * Handle a grid change from the kernel
   */
  protected onModelGridEnabled = () => {
    const { graph } = this;
    graph.setGridEnabled(this.model.get('grid_enabled'));
    graph.refresh();
  };

  /**
   * Handle a grid size change from the kernel
   */
  protected onModelGridSize = () => {
    const { graph } = this;
    graph.setGridSize(this.model.get('grid_size'));
    graph.refresh();
  };

  /**
   * Handle a grid color change from the kernel
   */
  protected onModelGridColor = () => {
    this.app.setGridColor(this.model.get('grid_color'));
  };

  /**
   * Handle a selected cell change from the kernel
   */
  protected onModelSelectedCells = () => {
    const { graph } = this;
    const cells: IMXCell[] = graph.getCellsById(this.model.get('selected_cells'));

    graph.selectionModel.setCells(cells);
  };

  /**
   * convenience method for frequently-called loops
   */
  protected idGetter(cellOrPage: IMXCell | IMXPage) {
    return cellOrPage.getId();
  }

  /**
   * Extract the cell or page ids
   */
  protected getCellIds(): string[] {
    return Object.values(this.graphModel.cells).map(this.idGetter);
  }

  /**
   * Translate drawio view translation to scroll offsets
   *
   * Ideally this would be the center of the viewport to allow for synced views
   */
  translateToScroll() {
    const { x, y } = this.graph.view.getTranslate();

    return { scroll_x: x, scroll_y: y };
  }

  /**
   * handle subscribed "native" mxEvents
   *
   * These are found throughout the code in the `mxEvent` namespace, though some
   * magic strings do appear duplicated in a numebr of placess
   */
  protected onDrawioEvent = (sender: IMXEventSource, event: IMXEvent) => {
    const { app, graph, model } = this;
    const { view } = graph;

    let change = {};

    switch (event.name) {
      case 'change':
        change = { selected_cells: graph.selectionModel.cells.map(this.idGetter) };
        break;
      case 'scale':
      case 'scaleAndTranslate':
        change = { zoom: view.getScale() };
        break;
      case 'pan':
      case 'translate':
      case 'size':
        change = this.translateToScroll();
        break;
      case 'pageSelected':
        change = {
          current_page: app.pages.indexOf(app.currentPage),
          page_ids: app.pages.map((p) => p.getId()),
        };
        break;
      case 'pageFormatChanged':
        change = { page_format: graph.pageFormat };
        break;
      case 'gridEnabledChanged':
        change = { grid_enabled: graph.gridEnabled };
        break;
      case 'gridSizeChanged':
        change = { grid_size: graph.gridSize };
        break;
      case 'gridColorChanged':
        change = { grid_color: view.gridColor };
        break;
      case 'removeCells':
      case 'cellsAdded':
      case 'cellsInserted':
        change = { cell_ids: this.getCellIds() };
        break;
      case 'fireMouseEvent':
        break; // these are too noisy, even for us
      default:
        DEBUG && console.warn('unhandled', event.name, event, 'from', sender);
        break;
    }

    const old: any = {};

    for (const k of Object.keys(change)) {
      old[k] = model.attributes[k];
    }

    if (!JSONExt.deepEqual(old, change)) {
      model.set(change);
      this.touch();
    }
  };
}
