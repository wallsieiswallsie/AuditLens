import { createServer } from './server.js';

try {
  const server = await createServer();

  await server.start();

  console.log(`AuditLens API listening at ${server.info.uri}`);

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.once(signal, async () => {
      await server.stop({ timeout: 5000 });
      process.exit(0);
    });
  }
} catch (error) {
  console.error('API startup failed:', error);
  process.exit(1);
}