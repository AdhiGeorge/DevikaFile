from .planner import Planner
from .researcher import Researcher
from .formatter import Formatter
from .coder import Coder
from .action import Action
from .internal_monologue import InternalMonologue
from .answer import Answer
from .runner import Runner
from .feature import Feature
from .patcher import Patcher
from .reporter import Reporter
from .decision import Decision

from src.project import ProjectManager
from src.state import AgentState
from src.logger import Logger

from src.bert.sentence import SentenceBert
from src.memory import KnowledgeBase
from src.browser.search import SearchEngine
from src.browser import Browser
from src.browser import start_interaction
from src.filesystem import ReadCode
from src.services import Netlify
from src.documenter.pdf import PDF

import json
import time
import platform
import tiktoken
import asyncio
import logging
from src.llm.llm import LLM
from src.utils.token_tracker import TokenTracker
from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from src.socket_instance import emit_agent

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Prometheus metrics
LLM_CALLS = Counter('llm_calls_total', 'Total number of LLM calls', ['model'])
SEARCH_CALLS = Counter('search_calls_total', 'Total number of search calls', ['engine'])
LLM_LATENCY = Histogram('llm_latency_seconds', 'LLM call latency in seconds', ['model'])
SEARCH_LATENCY = Histogram('search_latency_seconds', 'Search call latency in seconds', ['engine'])

class Agent:
    def __init__(self, base_model: str, search_engine: str, browser: Browser = None):
        if not base_model:
            raise ValueError("base_model is required")

        self.logger = Logger()

        """
        Accumulate contextual keywords from chained prompts of all preparation agents
        """
        self.collected_context_keywords = []

        """
        Agents
        """
        self.planner = Planner(base_model=base_model)
        self.researcher = Researcher(base_model=base_model)
        self.formatter = Formatter(base_model=base_model)
        self.coder = Coder(base_model=base_model)
        self.action = Action(base_model=base_model)
        self.internal_monologue = InternalMonologue(base_model=base_model)
        self.answer = Answer(base_model=base_model)
        self.runner = Runner(base_model=base_model)
        self.feature = Feature(base_model=base_model)
        self.patcher = Patcher(base_model=base_model)
        self.reporter = Reporter(base_model=base_model)
        self.decision = Decision(base_model=base_model)

        self.project_manager = ProjectManager()
        self.agent_state = AgentState()
        self.engine = search_engine
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        # Use the provided base_model for the root LLM instance as well.
        self.llm = LLM(model_id=base_model)
        self.search_engine = SearchEngine()
        self.token_tracker = TokenTracker()

    async def open_page(self, project_name, url):
        browser = await Browser().start()

        await browser.go_to(url)
        _, raw = await browser.screenshot(project_name)
        data = await browser.extract_text()
        await browser.close()

        return browser, raw, data

    async def execute(self, prompt: str, project_name: str) -> str:
        with tracer.start_as_current_span("agent_execute") as span:
            span.set_attribute("prompt", prompt)
            try:
                start_time = time.time()
                # Use asynchronous inference to avoid nested event loops
                response = await self.llm.ainference(prompt, project_name)
                latency = time.time() - start_time
                LLM_CALLS.labels(model=self.llm.model_id).inc()
                LLM_LATENCY.labels(model=self.llm.model_id).observe(latency)
                span.set_status(Status(StatusCode.OK))
                return response
            except Exception as e:
                logger.error(f"Agent execution error: {str(e)}")
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def search_queries(self, queries: list, project_name: str) -> dict:
        with tracer.start_as_current_span("agent_search_queries") as span:
            span.set_attribute("queries", json.dumps(queries))
            results = {}
            knowledge_base = KnowledgeBase()
            web_search = SearchEngine()
            self.logger.info(f"\nSearch Engine :: {web_search.primary_engine}")

            for query in queries:
                query = query.strip().lower()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                web_search.search(query)

                link = web_search.get_first_link()
                print("\nLink :: ", link, '\n')
                if not link:
                    continue
                browser, raw, data = loop.run_until_complete(self.open_page(project_name, link))
                emit_agent("screenshot", {"data": raw, "project_name": project_name}, False)
                results[query] = self.formatter.execute(data, project_name)

                self.logger.info(f"got the search results for : {query}")
            span.set_status(Status(StatusCode.OK))
            return results

    def update_contextual_keywords(self, sentence: str):
        with tracer.start_as_current_span("update_contextual_keywords") as span:
            span.set_attribute("sentence", sentence)
            keywords = SentenceBert(sentence).extract_keywords()
            for keyword in keywords:
                self.collected_context_keywords.append(keyword[0])
            span.set_status(Status(StatusCode.OK))
            return self.collected_context_keywords

    def make_decision(self, prompt: str, project_name: str) -> str:
        decision = self.decision.execute(prompt, project_name)

        for item in decision:
            function = item["function"]
            args = item["args"]
            reply = item["reply"]

            self.project_manager.add_message_from_agent(project_name, reply)

            if function == "git_clone":
                url = args["url"]
                # Implement git clone functionality here

            elif function == "generate_pdf_document":
                user_prompt = args["user_prompt"]
                # Call the reporter agent to generate the PDF document
                markdown = self.reporter.execute([user_prompt], "", project_name)
                _out_pdf_file = PDF().markdown_to_pdf(markdown, project_name)

                project_name_space_url = project_name.replace(" ", "%20")
                pdf_download_url = "http://127.0.0.1:1337/api/download-project-pdf?project_name={}".format(
                    project_name_space_url)
                response = f"I have generated the PDF document. You can download it from here: {pdf_download_url}"

                #asyncio.run(self.open_page(project_name, pdf_download_url))

                self.project_manager.add_message_from_agent(project_name, response)

            elif function == "browser_interaction":
                user_prompt = args["user_prompt"]
                # Call the interaction agent to interact with the browser
                start_interaction(self.base_model, user_prompt, project_name)

            elif function == "coding_project":
                user_prompt = args["user_prompt"]
                # Call the planner, researcher, coder agents in sequence
                plan = self.planner.execute(user_prompt, project_name)
                planner_response = self.planner.parse_response(plan)

                research = self.researcher.execute(plan, self.collected_context_keywords, project_name)
                search_results = self.search_queries(research["queries"], project_name)

                code = self.coder.execute(
                    step_by_step_plan=plan,
                    user_context=research["ask_user"],
                    search_results=search_results,
                    project_name=project_name
                )
                self.coder.save_code_to_project(code, project_name)

    def subsequent_execute(self, prompt: str, project_name: str):
        """
        Subsequent flow of execution
        """
        # Persist the previous agent response **once**
        # (it was already generated by Agent.execute and passed here as `prompt`).
        self.project_manager.add_message_from_agent(project_name, prompt)

        os_system = platform.platform()

        self.agent_state.set_agent_active(project_name, True)

        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        response, action = self.action.execute(conversation, project_name)

        self.project_manager.add_message_from_agent(project_name, response)

        print("\naction :: ", action, '\n')

        if action == "answer":
            # Answer.execute expects (question, context, project_name)
            response = self.answer.execute(conversation, code_markdown, project_name)
            self.project_manager.add_message_from_agent(project_name, response)

        elif action == "run":
            project_path = self.project_manager.get_project_path(project_name)
            self.runner.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                os_system=os_system,
                project_path=project_path,
                project_name=project_name
            )

        elif action == "deploy":
            deploy_metadata = Netlify().deploy(project_name)
            deploy_url = deploy_metadata["deploy_url"]

            response = {
                "message": "Done! I deployed your project on Netlify.",
                "deploy_url": deploy_url
            }
            response = json.dumps(response, indent=4)

            self.project_manager.add_message_from_agent(project_name, response)

        elif action == "feature":
            code = self.feature.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                system_os=os_system,
                project_name=project_name
            )
            print("\nfeature code :: ", code, '\n')
            self.feature.save_code_to_project(code, project_name)

        elif action == "bug":
            code = self.patcher.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                commands=None,
                error=prompt,
                system_os=os_system,
                project_name=project_name
            )
            print("\nbug code :: ", code, '\n')
            self.patcher.save_code_to_project(code, project_name)

        elif action == "report":
            markdown = self.reporter.execute(conversation, code_markdown, project_name)

            _out_pdf_file = PDF().markdown_to_pdf(markdown, project_name)

            project_name_space_url = project_name.replace(" ", "%20")
            pdf_download_url = "http://127.0.0.1:1337/api/download-project-pdf?project_name={}".format(
                project_name_space_url)
            response = f"I have generated the PDF document. You can download it from here: {pdf_download_url}"

            #asyncio.run(self.open_page(project_name, pdf_download_url))

            self.project_manager.add_message_from_agent(project_name, response)

        self.agent_state.set_agent_active(project_name, False)
        self.agent_state.set_agent_completed(project_name, True)
