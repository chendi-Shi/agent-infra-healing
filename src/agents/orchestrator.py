"""
Agent orchestrator - coordinates diagnosis, strategy, and execution agents.
"""
import os
import time
import logging
from typing import Dict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple agents for infrastructure healing."""

    def __init__(self, model: str, monitor, collector):
        self.monitor = monitor
        self.collector = collector
        self.logger = logger

        # Initialize LLM
        if 'claude' in model.lower():
            self.llm = ChatAnthropic(
                model=model,
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
                temperature=0.7
            )
        else:
            self.llm = ChatOpenAI(
                model=model,
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.7
            )

        self.logger.info(f"Initialized with model: {model}")

        # Build agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the multi-agent workflow graph."""
        # For now, a simple sequential graph
        # In Phase 2, we'll make this more sophisticated

        workflow = StateGraph(dict)

        # Define nodes
        workflow.add_node("monitor", self._monitor_node)
        workflow.add_node("diagnose", self._diagnose_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)

        # Define edges
        workflow.set_entry_point("monitor")
        workflow.add_edge("monitor", "diagnose")
        workflow.add_edge("diagnose", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", END)

        return workflow.compile()

    def _monitor_node(self, state: Dict) -> Dict:
        """Monitoring node - detect anomalies."""
        self.logger.info("Running monitoring...")

        # Check connectivity
        connectivity = self.monitor.check_connectivity()
        if not all(connectivity.values()):
            self.logger.warning(f"Some services unreachable: {connectivity}")

        # Detect anomalies
        anomalies = self.monitor.detect_anomalies()

        state['anomalies'] = anomalies
        state['has_issues'] = len(anomalies) > 0

        if anomalies:
            self.logger.warning(f"Detected {len(anomalies)} anomalies")
            for anomaly in anomalies:
                self.logger.warning(f"  - {anomaly['type']}: {anomaly['message']}")

        return state

    def _diagnose_node(self, state: Dict) -> Dict:
        """Diagnosis node - analyze root cause."""
        if not state.get('has_issues'):
            state['diagnosis'] = None
            return state

        self.logger.info("Running diagnosis...")

        anomalies = state['anomalies']

        # Collect fault data
        fault_data = self.collector.collect_fault_data(anomalies)

        # Use LLM to diagnose
        prompt = self._build_diagnosis_prompt(anomalies, fault_data)

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert infrastructure diagnosis agent. Analyze the fault data and identify root causes."),
                HumanMessage(content=prompt)
            ])

            diagnosis = response.content
            state['diagnosis'] = diagnosis
            state['fault_data'] = fault_data

            self.logger.info(f"Diagnosis complete:\n{diagnosis}")

        except Exception as e:
            self.logger.error(f"Diagnosis failed: {e}")
            state['diagnosis'] = f"Error during diagnosis: {e}"

        return state

    def _plan_node(self, state: Dict) -> Dict:
        """Planning node - generate recovery strategy."""
        if not state.get('diagnosis'):
            state['plan'] = None
            return state

        self.logger.info("Generating recovery plan...")

        diagnosis = state['diagnosis']
        anomalies = state['anomalies']

        prompt = self._build_planning_prompt(diagnosis, anomalies)

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert infrastructure recovery planner. Generate actionable recovery plans."),
                HumanMessage(content=prompt)
            ])

            plan = response.content
            state['plan'] = plan

            self.logger.info(f"Recovery plan:\n{plan}")

        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            state['plan'] = f"Error during planning: {e}"

        return state

    def _execute_node(self, state: Dict) -> Dict:
        """Execution node - apply recovery actions."""
        if not state.get('plan'):
            state['result'] = 'No action needed'
            return state

        self.logger.info("Executing recovery plan...")

        # For Phase 1, we just log the plan
        # In Phase 2, we'll actually execute actions

        plan = state['plan']

        # Save scenario for training
        scenario = {
            'anomalies': state['anomalies'],
            'diagnosis': state['diagnosis'],
            'plan': plan,
            'fault_data': state.get('fault_data', {})
        }

        filepath = self.collector.save_scenario(scenario)
        self.logger.info(f"Saved scenario to: {filepath}")

        state['result'] = 'Plan logged for review (auto-execution disabled in Phase 1)'

        return state

    def _build_diagnosis_prompt(self, anomalies: List[Dict], fault_data: Dict) -> str:
        """Build diagnosis prompt."""
        prompt = "# Fault Diagnosis Request\n\n"
        prompt += "## Detected Anomalies\n"
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"{i}. **{anomaly['type']}** (Severity: {anomaly['severity']})\n"
            prompt += f"   - {anomaly['message']}\n"
            if 'value' in anomaly:
                prompt += f"   - Value: {anomaly['value']}\n"

        prompt += "\n## Metrics\n"
        for service, metrics in fault_data.get('metrics', {}).items():
            prompt += f"**{service}**:\n"
            for key, value in metrics.items():
                prompt += f"  - {key}: {value}\n"

        if fault_data.get('logs'):
            prompt += "\n## Recent Error Logs (sample)\n"
            for log in fault_data['logs'][:5]:
                prompt += f"- {log.get('message', str(log))}\n"

        prompt += "\n## Task\n"
        prompt += "Analyze the above data and provide:\n"
        prompt += "1. Root cause analysis\n"
        prompt += "2. Confidence level (high/medium/low)\n"
        prompt += "3. Related components\n"

        return prompt

    def _build_planning_prompt(self, diagnosis: str, anomalies: List[Dict]) -> str:
        """Build planning prompt."""
        prompt = "# Recovery Planning Request\n\n"
        prompt += "## Diagnosis\n"
        prompt += diagnosis + "\n\n"

        prompt += "## Current Issues\n"
        for anomaly in anomalies:
            prompt += f"- {anomaly['message']}\n"

        prompt += "\n## Task\n"
        prompt += "Generate a recovery plan with:\n"
        prompt += "1. Immediate actions to restore service\n"
        prompt += "2. Commands or API calls to execute\n"
        prompt += "3. Verification steps\n"
        prompt += "4. Rollback plan if recovery fails\n"

        return prompt

    def run(self, interval: int = 30):
        """Run the agent system in a loop."""
        self.logger.info(f"Starting agent loop (interval: {interval}s)")

        while True:
            try:
                # Run the agent workflow
                state = {'timestamp': time.time()}
                result = self.graph.invoke(state)

                if not result.get('has_issues'):
                    self.logger.info("✓ No issues detected")
                else:
                    self.logger.info(f"✓ Workflow complete: {result.get('result')}")

                # Wait before next iteration
                time.sleep(interval)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"Error in agent loop: {e}", exc_info=True)
                time.sleep(interval)
