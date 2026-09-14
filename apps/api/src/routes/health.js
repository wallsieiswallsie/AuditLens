import { health } from '../handlers/health.js';
export const healthRoute = { method: 'GET', path: '/health', handler: health };

