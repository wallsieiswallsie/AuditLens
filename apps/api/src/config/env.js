import dotenv from 'dotenv';
import { fileURLToPath } from 'node:url';

dotenv.config({ path: fileURLToPath(new URL('../../../../.env', import.meta.url)) });

export function readConfig(env = process.env) {
  const integer = (key, fallback) => {
    const value = env[key] || String(fallback);
    if (!/^\d+$/.test(value) || Number(value) < 1 || Number(value) > 65535) {
      throw new Error(`Invalid ${key}: expected a port from 1 to 65535`);
    }
    return Number(value);
  };
  return {
    nodeEnv: env.NODE_ENV || 'development',
    api: { host: env.API_HOST || '127.0.0.1', port: integer('API_PORT', 3001) },
    database: {
      host: env.DATABASE_HOST || '127.0.0.1',
      port: integer('DATABASE_PORT', 5432),
      database: env.DATABASE_NAME || 'auditlens',
      user: env.DATABASE_USER || 'auditlens_dev',
      password: env.DATABASE_PASSWORD || '',
    },
  };
}

