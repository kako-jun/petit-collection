import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://kako-jun.github.io/petit-collection',
  base: '/',
  trailingSlash: 'ignore',
  build: {
    assets: '_assets',
  },
});
