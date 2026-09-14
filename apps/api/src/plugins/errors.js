export const errorsPlugin = {
  name: 'safe-errors',
  register: async (server) => {
    server.ext('onPreResponse', (request, h) => {
      const response = request.response;
      if (response.isBoom && response.output.statusCode >= 500) {
        return h.response({ statusCode: 500, error: 'Internal Server Error', message: 'An unexpected error occurred' }).code(500);
      }
      return h.continue;
    });
  },
};

