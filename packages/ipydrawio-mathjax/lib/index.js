import { URLExt, PageConfig } from '@jupyterlab/coreutils';
/**
 * The path on the server to base application HTML, to be served in an iframe
 */
export const DRAWIO_MATHJAX_URL = URLExt.join(
  PageConfig.getOption('fullLabextensionsUrl'),
  '@deathbeds/ipydrawio-mathjax/static/dio/'
);
