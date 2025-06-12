import asyncio
import logging
from flask import Flask
from flask_socketio import SocketIO
from src.agents.agent import Agent
from src.config import Config
from src.logger import Logger
from src.apis.project import project_bp
from src.socket_instance import socketio, emit_agent
from prometheus_client import start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add console exporter for development
console_exporter = ConsoleSpanExporter()
span_processor = BatchSpanProcessor(console_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create Flask app
app = Flask(__name__)
app.register_blueprint(project_bp)

# Initialize Flask-SocketIO
socketio.init_app(app)

# Start Prometheus metrics server
config = Config()
start_http_server(config.monitoring.metrics.prometheus.port)

# Initialize agent
agent = Agent(
    base_model=config.azure_openai.model,
    search_engine=config.search_engines.primary
)

# Socket event handlers
@socketio.on('socket_connect')
def handle_socket_connect(data):
    logger.info("Socket connected: %s", data)

@socketio.on('user-message')
def handle_user_message(data):
    logger.info("User message received: %s", data)
    # Example: Echo back the message
    emit_agent("user-message", data)

async def main():
    # Example usage
    project_name = "test_project"
    prompt = "Create a simple Python web server using FastAPI"
    try:
        response = await agent.execute(prompt, project_name)
        logger.info(f"Agent response: {response}")
        agent.make_decision(response, project_name)
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the Flask-SocketIO server
    socketio.run(app, debug=False, port=1337, host="0.0.0.0")
