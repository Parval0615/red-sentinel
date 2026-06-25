from __future__ import annotations

from agent_integration_system.config.schema import AgentConfig
from agent_integration_system.profile.schema import AgentSecurityProfile, ProfileNode, ProfileTool

RISK_SURFACES_BY_NODE_TYPE: dict[str, list[str]] = {
    "input_node": ["prompt_injection", "jailbreak"],
    "rag_retriever": ["indirect_prompt_injection", "knowledge_poisoning", "unauthorized_retrieval"],
    "tool_node": ["tool_abuse", "privilege_escalation", "parameter_tampering"],
    "memory_node": ["memory_poisoning", "cross_session_leakage"],
    "llm_node": ["goal_drift", "instruction_hijacking"],
    "output_node": ["pii_leakage", "unsafe_output"],
}


def build_agent_security_profile(config: AgentConfig) -> AgentSecurityProfile:
    return AgentSecurityProfile(
        agent_name=config.agent.name,
        framework=config.agent.framework,
        root_path=config.agent.root_path,
        entrypoint=config.agent.entrypoint,
        business_domain=config.business.domain,
        nodes=[
            ProfileNode(
                id=node.id,
                type=node.type,
                target=node.target,
                risk_surfaces=list(RISK_SURFACES_BY_NODE_TYPE[node.type]),
                defenses=node.defenses,
            )
            for node in config.nodes
        ],
        tools=[
            ProfileTool(
                name=tool.name,
                risk_level=tool.risk_level,
                allowed_roles=tool.allowed_roles,
                side_effect=tool.side_effect,
            )
            for tool in config.tools
        ],
        attack_entries=config.evaluation.attack_entries,
        sensitive_data=config.business.sensitive_data,
        rag_enabled=config.rag.enabled,
    )
