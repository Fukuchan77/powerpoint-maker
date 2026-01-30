# PowerPoint Maker

An AI-powered application that generates PowerPoint presentations from a template and a topic.

## Features

- **Template Analysis**: Upload your corporate or custom PowerPoint templates.
- **AI Research**: Automatically researches the provided topic using advanced AI agents.
- **Content Generation**: Generates slide content structured to fit your template's layout.
- **PowerPoint Generation**: Produces a downloadable `.pptx` file with preserved formatting.
- **Preview**: Review and edit the generated content before downloading.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) (Recommended)
- Or: Python 3.12+ and Node.js (LTS)

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    mise install
    ```
    (Or manually install backend dependencies with `uv` and frontend with `pnpm`)

### Usage

1.  Start the development servers:
    ```bash
    mise run dev
    ```
2.  Open your browser to `http://localhost:5173`.
3.  Upload a PowerPoint template (`.pptx`).
4.  Enter a topic (e.g., "The Future of AI").
5.  Click "Generate Content".
6.  Review the proposed slides and click "Download PowerPoint".

## License

[MIT](LICENSE)
