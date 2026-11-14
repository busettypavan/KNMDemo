// Runs before every test file: Testing Library's DOM matchers and the browser APIs jsdom does not provide.
import '@testing-library/jest-dom';

// node-environment test files share this setup file and have no window
if (typeof window !== 'undefined') {
  // on the prototype, so a polyfill survives a test deleting the own property of the same name
  const proto = Object.getPrototypeOf(window) as any;
  if (!window.matchMedia) {
    proto.matchMedia = (query: string) => ({ matches: false, media: query, onchange: null, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false });
  }
  if (!(window as any).ResizeObserver) {
    proto.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  }
  if (!window.scrollTo || String(window.scrollTo).includes('not implemented')) window.scrollTo = (() => undefined) as typeof window.scrollTo;
}
