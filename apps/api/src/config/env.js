import dotenv from 'dotenv';
import { fileURLToPath } from 'node:url';

dotenv.config({
  path: fileURLToPath(new URL('../../../../.env', import.meta.url)),
});

export function readConfig(env = process.env) {
  if (env.NODE_ENV === 'production') requireDatabaseUrl(env);
  const integer = (key, fallback) => {
    const value = env[key] || String(fallback);

    if (
      !/^\d+$/.test(value) ||
      Number(value) < 1 ||
      Number(value) > 65535
    ) {
      throw new Error(`Invalid ${key}: expected a port from 1 to 65535`);
    }

    return Number(value);
  };

  return {
    nodeEnv: env.NODE_ENV || 'development',
    api: {
      host: env.API_HOST || '0.0.0.0',
      port: integer('PORT', 3001),
    },
    database: env.DATABASE_URL,
  };
}

// Database-free health and offline generation do not require a connection.
export function requireDatabaseUrl(env = process.env) {
  const value = env.DATABASE_URL?.trim();

  if (!value) {
    throw new Error('Missing required environment variable: DATABASE_URL');
  }

  try {
    const url = new URL(value);

    if (
      !['postgres:', 'postgresql:'].includes(url.protocol) ||
      !url.hostname
    ) {
      throw new Error();
    }
  } catch {
    throw new Error(
      'Invalid DATABASE_URL: expected a PostgreSQL connection URL'
    );
  }

  return value;
}
