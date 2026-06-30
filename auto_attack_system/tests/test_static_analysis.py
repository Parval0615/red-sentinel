from __future__ import annotations

from pathlib import Path

from auto_attack_system.ingestion.static_analysis import CodeStaticAnalyzer, analyze_source_static


def test_static_analysis_detects_framework(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
import langgraph
from langgraph import StateGraph

def run_agent():
    pass
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    assert result.framework is not None
    assert result.framework.framework == "langgraph"
    assert result.framework.confidence > 0.0


def test_static_analysis_detects_risk_surfaces(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
def execute_tool(action):
    return action()

def retrieve_docs(query):
    return []

def store_memory(key, value):
    pass
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    assert "tool_tampering" in result.risk_surfaces
    assert "knowledge_poisoning" in result.risk_surfaces
    assert "memory_poisoning" in result.risk_surfaces


def test_static_analysis_detects_sensitive_patterns(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
API_KEY = "sk-1234567890"
PASSWORD = "secret123"
DB_URL = "postgresql://user:pass@localhost/db"
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    categories = {pattern.category for pattern in result.sensitive_data}
    assert "API_KEY" in categories
    assert "PASSWORD" in categories
    assert "DATABASE_CREDENTIAL" in categories


def test_static_analysis_detects_unsafe_code(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
def dangerous_exec(code):
    exec(code)

def dangerous_eval(data):
    return eval(data)

def run_command(cmd):
    import subprocess
    subprocess.Popen(cmd, shell=True)
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    high_severity = [f for f in result.findings if f.severity == "high"]
    assert len(high_severity) >= 2
    finding_codes = {f.finding_id.split("-")[0] for f in result.findings}
    assert "EXEC_STATEMENT" in finding_codes
    assert "EVAL_STATEMENT" in finding_codes


def test_static_analysis_extracts_tool_signatures(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
def lookup_order(order_id: str, customer_id: str):
    pass

async def refund_order(order_id: str):
    pass
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    assert len(result.tool_signatures) == 2
    names = {sig["name"] for sig in result.tool_signatures}
    assert {"lookup_order", "refund_order"} <= names
    lookup = next(sig for sig in result.tool_signatures if sig["name"] == "lookup_order")
    assert lookup["parameters"] == ["order_id", "customer_id"]
    refund = next(sig for sig in result.tool_signatures if sig["name"] == "refund_order")
    assert refund["is_async"] is True


def test_static_analysis_identifies_node_candidates(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
def normalize_input(request):
    pass

def retrieve_documents(query):
    pass

def execute_tool_call(tool_name, args):
    pass

def format_output(response):
    pass
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    node_types = {candidate["type"] for candidate in result.node_candidates}
    assert {"input_node", "rag_retriever", "tool_node", "output_node"} <= node_types


def test_static_analysis_excludes_venv_and_git(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    venv = src / ".venv"
    venv.mkdir()
    (venv / "site-packages").mkdir()
    git = src / ".git"
    git.mkdir()
    app = src / "app.py"
    app.write_text("def run():\n    pass", encoding="utf-8")
    (venv / "fake.py").write_text("secret = 'hidden'", encoding="utf-8")

    result = analyze_source_static(src)

    assert result.files_scanned == 1
    assert result.files_skipped == 0


def test_static_analysis_empty_project(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()

    result = analyze_source_static(src)

    assert result.files_scanned == 0
    assert result.confidence == 0.4
    assert "Static analysis completed on 0 Python files." in result.notes


def test_static_analysis_confidence_calculation(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text(
        """
import langchain
from langchain.chains import LLMChain

def process_input(text):
    pass

def call_tool(name, args):
    pass
""".strip(),
        encoding="utf-8",
    )

    result = analyze_source_static(src)

    assert result.confidence > 0.5
    assert result.confidence <= 1.0


def test_code_static_analyzer_class_api(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    app = src / "app.py"
    app.write_text("def main():\n    return 'hello'", encoding="utf-8")

    analyzer = CodeStaticAnalyzer(src)
    result = analyzer.analyze()

    assert result.root_path == str(src.resolve())
    assert result.files_scanned == 1
