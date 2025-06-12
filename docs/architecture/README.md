# Agent Architecture

## Overview

Agent is a modern, async, and scalable agent orchestration framework. It leverages state-of-the-art language models like **Claude** and **GPT-4** for natural language understanding, generation, and reasoning.

## Core Components

1. **User Interface**: A web-based chat interface for interacting with Agent, viewing project files, and monitoring the agent's state.
2. **Core System**: The main application logic that coordinates between different components and manages the agent's workflow.
3. **Large Language Models**: Agent leverages state-of-the-art language models like **Claude** and **GPT-4** for natural language understanding, generation, and reasoning.
4. **Planning Module**: Responsible for breaking down complex tasks into manageable steps and creating execution plans.
5. **Research Module**: Handles web searches and information gathering to support the development process.
6. **Coding Module**: Generates and manages code based on the plan and research.
7. **Execution Module**: Safely executes generated code in a controlled environment.
8. **Knowledge Base**: Local Qdrant-based vector store for persistent knowledge.

## Async/Await

All agent and service methods are async for better performance. This includes:
- LLM inference
- Web search
- Knowledge base operations
- Agent orchestration

## Caching

In-memory caching is used for expensive operations:
- Embeddings
- Keyword extraction
- Search results
- LLM completions (where safe)

## Rate Limiting

In-memory rate limiting is implemented for API calls:
- LLM API calls
- Search API calls
- Knowledge base operations

## Error Handling & Retries

Robust error handling and retry logic is implemented for all network/API calls:
- Configurable retry counts
- Exponential backoff
- Detailed error logging

## Monitoring

- **Prometheus**: Metrics for API calls, errors, latency, etc.
- **Logging**: Structured logging (JSON format).
- **Tracing**: OpenTelemetry tracing for detailed execution flow.

## Cost Tracking

- Token and cost tracking for every LLM and search API call.
- Aggregated cost reporting for the run/session.

## Project Structure

```
.
├── agent/                  # Core agent logic
│   ├── core/               # Core agent modules (orchestrator, knowledge base)
│   ├── utils/              # Utility functions
│   ├── memory/             # Memory management
│   ├── llm/                # LLM integration
│   └── services/           # External service integrations
├── src/                    # Source code
│   ├── agents/             # Agent implementations
│   ├── bert/               # BERT/KeyBERT for keyword extraction
│   ├── browser/            # Web search and browser automation
│   ├── llm/                # LLM client and inference
│   ├── services/           # Service integrations
│   └── utils/              # Utility functions
├── ui/                     # Web UI (Svelte)
├── data/                   # Data storage (cache, logs, projects)
├── docs/                   # Documentation
├── tests/                  # Unit and integration tests
├── config.yaml             # Configuration file
├── .env                    # Environment variables (API keys)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Configuration

- **API Keys**: Store all API keys in `.env`.
- **Configurable Values**: All configurable values are in `config.yaml`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
