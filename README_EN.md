# openapi-gen (English)

> VS Code Copilot skill that auto-generates OpenAPI 3.1.0 specs + Redoc docs from source code

## Features

- **Fully automatic**: reads project source code and reverse-engineers all API endpoints
- **Rich annotations**: every path, parameter, and field includes Chinese descriptions
- **Complete coverage**: recursively scans route registrations, controller annotations, and middleware routes
- **Visual docs**: generates a Redoc HTML page alongside the YAML spec
- **Built-in validation**: includes a validation script to verify YAML structure and reference integrity

## Supported Frameworks

| Language | Frameworks |
|----------|-----------|
| Java | Spring Boot, Spring Cloud, Quarkus |
| Go | Gin, Echo, Fiber |
| Python | Django / DRF, FastAPI, Flask |
| Node.js | Express, NestJS, Koa |
| PHP | Laravel, ThinkPHP, Symfony |
| C# | ASP.NET Core, ABP, NancyFX |
| Rust | Axum, Actix Web, Rocket |

## Installation

```bash
# Via skills.sh (recommended)
skills install gh:your-username/openapi-gen

# Or manually copy into your project
cp -r openapi-gen/ your-project/.agents/skills/openapi-gen
```

## Usage

In VS Code Copilot Chat, type:

```
Generate OpenAPI spec for this project
```

The skill will automatically detect the tech stack, scan all endpoints, and generate:

```
openapi_gen/
├── openapi.yaml   # OpenAPI 3.1.0 specification
└── index.html     # Redoc visualization page
```

### View the docs

```bash
npx serve openapi_gen
# or
python -m http.server -d openapi_gen
```

Open `http://localhost:3000` (or `8000`) in your browser.

## License

[MIT](LICENSE)
