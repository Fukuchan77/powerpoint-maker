# Frontend - PowerPoint Maker

This is the React-based frontend for the PowerPoint Maker application.

## Tech Stack

- **Framework**: React 19 (Vite)
- **Language**: TypeScript
- **Styling**: CSS Modules / Vanilla CSS
- **Testing**: Vitest, React Testing Library, Playwright
- **HTTP Client**: Axios

## Setup

1.  Install dependencies:
    ```bash
    pnpm install
    ```

## Scripts

- `pnpm dev`: Start the development server.
- `pnpm build`: Build for production.
- `pnpm lint`: Run ESLint.
- `pnpm test`: Run unit/component tests (Vitest).
- `pnpm test:e2e`: Run end-to-end tests (Playwright).

## Project Structure

- `src/components`: Reusable UI components.
- `src/types.ts`: TypeScript interfaces matching the backend schemas.
- `e2e`: Playwright end-to-end tests.

## Testing

We use **Vitest** for unit testing and **Playwright** for E2E testing.

### Running Unit Tests
```bash
pnpm test
```

### Running E2E Tests
```bash
pnpm test:e2e
```
