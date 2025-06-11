## Agent's system architecture consists of the following key components:

1. **User Interface**: A web-based chat interface for interacting with Agent, viewing project files, and monitoring the agent's state.
2. **Core System**: The main application logic that coordinates between different components and manages the agent's workflow.
3. **Large Language Models**: Agent leverages state-of-the-art language models like **Claude**, **GPT-4**, and **Local LLMs via Ollama** for natural language understanding, generation, and reasoning.
4. **Planning Module**: Responsible for breaking down complex tasks into manageable steps and creating execution plans.
5. **Research Module**: Handles web searches and information gathering to support the development process.
6. **Code Generation**: Generates and modifies code based on requirements and best practices.
7. **Browser Interaction Module**: Enables Agent to navigate websites, extract information, and interact with web elements as needed.
8. **Project Management**: Manages project files, dependencies, and version control.
9. **State Management**: Tracks and maintains the agent's state throughout the development process.
10. **Configuration Management**: Handles system settings, API keys, and environment variables.

Read [ARCHITECTURE.md](https://github.com/stitionai/agent/Docs/architecture/ARCHITECTURE.md) for the detailed architecture of Agent.
Read [UNDER_THE_HOOD.md](https://github.com/stitionai/agent/Docs/architecture/UNDER_THE_HOOD.md) for the detailed working of Agent.
