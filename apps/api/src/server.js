import Hapi from '@hapi/hapi';
import { readConfig } from './config/env.js';
import { healthRoute } from './routes/health.js';
import { errorsPlugin } from './plugins/errors.js';

export async function createServer(config = readConfig()) {
  const server = Hapi.server({ ...config.api, routes: { payload: { maxBytes: 1048576 } } });
  await server.register(errorsPlugin);
  server.route(healthRoute);
  return server;
}