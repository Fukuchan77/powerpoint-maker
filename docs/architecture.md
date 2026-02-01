# PowerPoint Maker Architecture Documentation

## 📋 Overview

PowerPoint Maker is a web application that automatically generates PowerPoint presentations from templates and topics using AI technology.

## 🏗️ System Architecture

### Overall Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │ HTTP │   FastAPI   │ API  │   BeeAI     │
│  (React 19) │◄────►│   Backend   │◄────►│  Framework  │
│             │      │   (Python)  │      │   (LLM)     │
└─────────────┘      └─────────────┘      └─────────────┘
      │                      │                     │
      │                      ▼                     ▼
      │              ┌─────────────┐      ┌─────────────┐
      │              │  python-pptx│      │  DuckDuckGo │
      │              │   Library   │      │   Search    │
      │              └─────────────┘      └─────────────┘
      │
      ▼
┌─────────────┐
│  Local File │
│   Storage   │
└─────────────┘
```

## 🎯 Component Details

### Frontend (React + TypeScript)

**Technology Stack**:

- React 19
- TypeScript
- Vite (Build tool)
- Axios (HTTP client)
- Vitest + React Testing Library (Testing)
- Playwright (E2E testing)

**Main Components**:

```typescript
src/
├── components/
│   ├── TopicInput.tsx          // Topic input UI
│   ├── TemplateUploader.tsx    // Template upload
│   ├── Preview.tsx             // Preview display
│   └── ErrorBoundary.tsx       // Error handling
├── utils/
│   └── logger.ts               // Logging utility
├── types.ts                    // Type definitions
└── App.tsx                     // Main application
```

**Data Flow**:

1. User uploads template (.pptx)
2. Backend API analyzes template
3. User enters topic
4. Research API generates content (180 second timeout)
5. Preview display
6. Generate API creates PPTX file for download

### Backend (FastAPI + Python)

**Technology Stack**:

- FastAPI (Web framework)
- Python 3.12+
- BeeAI Framework (AI agent)
- python-pptx (PPTX generation)
- Pydantic (Data validation)
- Pytest (Testing)

**Layered Architecture**:

```python
backend/app/
├── api/                    # API Layer
│   └── routes.py          # HTTP endpoint definitions
├── services/              # Service Layer
│   ├── generator.py       # PPTX generation logic
│   ├── research.py        # Research agent
│   └── template.py        # Template analysis
├── core/                  # Core Layer
│   ├── llm.py            # LLM integration
│   └── logging.py        # Logging configuration
├── middleware/           # Middleware
│   └── rate_limit.py     # Rate limiting
├── schemas.py            # Data schemas
├── config.py             # Configuration management
└── main.py               # Application entry point
```

## 🔄 Data Flow

### 1. Template Analysis Flow

```
User → Upload .pptx → POST /api/analyze-template
                            ↓
                    TemplateAnalyzer
                            ↓
                    Extract layouts & styles
                            ↓
                    Return TemplateInfo
                            ↓
                    Frontend stores template data
```

### 2. Content Generation Flow

```
User → Enter topic → POST /api/research?topic=xxx
                            ↓
                    ResearchAgent (BeeAI)
                            ↓
                    DuckDuckGo Search
                            ↓
                    LLM generates content
                            ↓
                    Structure to template layouts
                            ↓
                    Return SlideContent[]
                            ↓
                    Frontend displays preview
```

### 3. PPTX Generation Flow

```
User → Click "Download" → POST /api/generate
                            ↓
                    PresentationGenerator
                            ↓
                    Create new presentation
                            ↓
                    Apply template styles
                            ↓
                    Insert content & images
                            ↓
                    Return .pptx file
                            ↓
                    Browser downloads file
```

## 📋 API Schemas

### SlideContent Schema

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Slide title |
| `bullet_points` | List[string] | Simple bullet points (flat list) |
| `bullets` | List[BulletPoint] | Structured bullets with hierarchy support |
| `layout_index` | int | Template layout index to use |
| `image_url` | string (optional) | URL for slide image |
| `image_caption` | string (optional) | Caption for the image |
| `chart` | ChartData (optional) | Chart data for visualization |
| `theme_color` | string (optional) | Theme color (e.g., "ACCENT_1") |

**Note:** `bullet_points` and `bullets` are alternative representations:
- Use `bullet_points` for simple flat lists
- Use `bullets` when you need hierarchical structure with indentation levels

## 📊 Quality Metrics

### Test Coverage

| Component    | Coverage | Tests      | Status       |
| ------------ | -------- | ---------- | ------------ |
| **Backend**  | 93%      | 74 tests   | ✅ Excellent |
| **Frontend** | 93.47%   | 24 tests   | ✅ Excellent |
| **E2E**      | 100%     | 3 browsers | ✅ Perfect   |

### Performance Metrics

- **Template Analysis**: < 2 seconds
- **Content Generation**: 30-120 seconds (LLM dependent)
- **PPTX Generation**: < 5 seconds
- **Frontend Initial Load**: < 1 second

## 🔒 Security

### Implemented Security Measures

1. **File Validation**
   - MIME type checking
   - MIME type checking
   - File size limit (10MB)
   - Extension validation (.pptx only)

2. **Rate Limiting**
   - Global default: 100 requests/hour
   - Endpoint-specific limits:
     - `/api/analyze-template`: 10 requests/minute
     - `/api/research`: 10 requests/minute
     - `/api/generate`: 5 requests/minute
   - DDoS attack prevention
   - Per-client IP address tracking

3. **Input Sanitization**
   - Pydantic validation
   - XSS prevention

4. **Environment Variable Management**
   - Secure API key storage
   - `.env` file added to `.gitignore`

## 🎨 Design Principles

### SOLID Principles Applied

1. **Single Responsibility**: Each service has a single responsibility
2. **Open/Closed**: Extensible, closed for modification
3. **Liskov Substitution**: Interface consistency
4. **Interface Segregation**: Small interfaces
5. **Dependency Inversion**: Depend on abstractions

### Design Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic separation
- **Factory Pattern**: Object creation abstraction
- **Strategy Pattern**: Algorithm switching

## 🚀 Scalability

### Current Architecture

- **Monolithic**: Frontend + Backend separation
- **Stateless**: No session management
- **File-based**: Local storage

### Future Extensibility

1. **Microservices**
   - Template Service
   - Research Service
   - Generator Service

2. **Cloud Storage**
   - S3-compatible storage
   - CDN integration

3. **Caching**
   - Redis implementation
   - Template analysis result caching

4. **Async Processing**
   - Celery/RQ implementation
   - Background jobs

## 📚 Technical Constraints

### Limitations

1. **LLM Response Time**: 30-120 seconds (external API dependent)
2. **File Size**: Maximum 10MB
3. **Concurrent Connections**: Not configured (requires tuning)
4. **Browser Compatibility**: Modern browsers only (Chrome, Firefox, Safari)

### Dependencies

- **BeeAI Framework**: >= 0.1.76 (with DuckDuckGo support)
- **Python**: >= 3.12
- **Node.js**: >= 18 (LTS)

## 🔧 Troubleshooting

For details, see [troubleshooting.md](./troubleshooting.md).

## 📖 Related Documentation

- [Troubleshooting](./troubleshooting.md)
- [Development Guide](../CONTRIBUTING.md)
- [API Specification](http://localhost:8000/docs) (Development environment)

---

**Last Updated**: February 1, 2026  
**Version**: 0.1.0
