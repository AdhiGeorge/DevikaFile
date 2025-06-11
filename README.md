<img src=".assets/agent-avatar.png" alt="Agent Logo" width="250">

<h1 align="center">🚀 Agent - AI Software Engineer 👩‍💻</h1>

![agent screenshot](.assets/agent-screenshot.png)

Agent is an advanced AI software engineer that can understand high-level human instructions, break them down into steps, research relevant information, and write code to achieve the given objective. Agent utilizes large language models, planning and reasoning algorithms, and web browsing abilities to intelligently develop software.

Agent aims to revolutionize the way we build software by providing an AI pair programmer who can take on complex coding tasks with minimal human guidance. Whether you need to create a new feature, fix a bug, or develop an entire project from scratch, Agent is here to assist you.

> Agent is modeled after [Devin](https://www.cognition-labs.com/introducing-devin) by Cognition AI. This project aims to be an open-source alternative to Devin with an "overly ambitious" goal to meet the capabilities of Devin.

## Features

- 🤖 **AI Software Engineer**: An intelligent agent that can understand complex software development tasks and break them down into manageable steps.
- 🔍 **Web Research**: Ability to search the web for relevant information, documentation, and examples.
- 💻 **Code Generation**: Generates high-quality, production-ready code based on requirements and best practices.
- 🔄 **Interactive Development**: Engages in a conversation with users to clarify requirements and provide updates.
- 🛠️ **Multiple Language Support**: Can work with various programming languages and frameworks.
- 📚 **Documentation Generation**: Creates comprehensive documentation for the code it generates.
- 🔍 **Code Review**: Performs thorough code reviews and suggests improvements.
- 🐛 **Debugging**: Helps identify and fix bugs in the code.
- 📦 **Dependency Management**: Handles project dependencies and ensures compatibility.

## Installation

To install Agent, follow these steps:

1. Clone the Agent repository:
```bash
git clone https://github.com/stitionai/agent.git
```

2. Navigate to the project directory:
```bash
cd agent
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the required API keys and configurations (see Configuration section below).

5. Start the Agent server:
```bash
python agent.py
```

You should see output similar to:
```
root: INFO   : Agent is up and running!
```

6. In a new terminal, start the UI:
```bash
cd ui
npm install
npm run dev
```

7. Access the Agent web interface by opening a browser and navigating to `http://127.0.0.1:3001`

## Usage

To start using Agent, follow these steps:

1. Open the Agent web interface in your browser.
2. Create a new project or select an existing one.
3. Start a conversation with Agent by describing your software development task.
4. In the chat interface, provide a high-level objective or task description for Agent to work on.
5. Agent will process your request, break it down into steps, and start working on the task.
6. Monitor Agent's progress, view generated code, and provide additional guidance or feedback as needed.
7. Once Agent completes the task, review the generated code and project files.

## Configuration

Agent requires certain configuration settings and API keys to function properly:

when you first time run Agent, it will create a `config.toml` file for you in the root directory. You can configure the following settings in the settings page via UI:

- **OpenAI API Key**: Required for GPT-4 model access.
- **Anthropic API Key**: Required for Claude model access.
- **Google API Key**: Required for Google search functionality.
- **Bing API Key**: Required for Bing search functionality.
- **DuckDuckGo API Key**: Required for DuckDuckGo search functionality.
- **Tavily API Key**: Required for Tavily search functionality.
- **Model Selection**: Choose between GPT-4, Claude, or local models.
- **Search Engine Selection**: Choose between Google, Bing, DuckDuckGo, or Tavily.
- **Temperature**: Adjust the creativity level of the AI responses.
- **Max Tokens**: Set the maximum length of AI responses.
- **Context Window**: Configure the size of the context window for the AI model.

## Contributing

We welcome contributions to enhance Agent's capabilities and improve its performance. To contribute, please see the [`CONTRIBUTING.md`](CONTRIBUTING.md) file for steps.

## Issues and Discussions

If you encounter any issues or have questions, please check the [issue tracker](https://github.com/stitionai/agent/issues) or join the [discussions](https://github.com/stitionai/agent/discussions) for general discussions.

We also have a Discord server for the Agent community, where you can connect with other users, share your experiences, ask questions, and collaborate on the project. To join the Agent community Discord server, [click here](https://discord.gg/CYRp43878y).

## License

Agent is released under the [MIT License](https://opensource.org/licenses/MIT). See the `LICENSE` file for more information.

## Star History

<a href="https://star-history.com/#stitionai/agent&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=stitionai/agent&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=stitionai/agent&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=stitionai/agent&type=Date" />
  </picture>
</a>

## Acknowledgments

We would like to thank all the contributors and users who have helped make Agent what it is today. Special thanks to the open-source community for their invaluable contributions and support.

We hope you find Agent to be a valuable tool in your software development journey. If you have any questions, feedback, or suggestions, please don't hesitate to reach out. Happy coding with Agent!
