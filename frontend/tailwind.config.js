// The kit's templates use Tailwind utilities whose values are the design-system tokens
// (vendor/ui-kit/tailwind-preset.js); the app gets them by scanning the kit's sources too.
const uiKit = require('./vendor/ui-kit/tailwind-preset');

/** @type {import('tailwindcss').Config} */
module.exports = {
  presets: [uiKit],
  content: ['./src/**/*.{html,ts}', './vendor/ui-kit/src/lib/**/*.{html,ts}'],
};
