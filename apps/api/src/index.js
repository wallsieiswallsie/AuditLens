try {
  const { createServer } = await import('./server.js');
  const server = await createServer();

  await server.start();

  console.log(`AuditLens API listening at ${server.info.uri}`);

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.once(signal, async () => {
      await server.stop({ timeout: 5000 });
      process.exit(0);
    });
  }
} catch {
  console.error('API startup failed: check environment configuration and listener availability');
  process.exit(1);
}
