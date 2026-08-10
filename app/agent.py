import re
from dataclasses import dataclass

KNOWLEDGE_BASE = {
    "cloud": "Cloud infrastructure gồm compute, storage, networking, security/IAM và các dịch vụ vận hành.",
    "docker": "Docker giúp đóng gói app cùng dependencies để giảm lỗi 'it works on my machine'.",
    "health": "Health check cho biết process còn sống; readiness cho biết service đã sẵn sàng nhận traffic.",
    "security": "Production cần secrets trong environment, API key/JWT, rate limiting và cost guard.",
    "scaling": "Muốn scale ngang, agent nên stateless; session/cache nên đưa ra Redis hoặc database dùng chung.",
    "observability": "Observability gồm logs, metrics và traces để debug trước khi người dùng phàn nàn.",
}

@dataclass
class AgentResponse:
    answer: str
    citations: list[str]
    tokens_estimated: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 8)


class MockAgent:
    """A tiny deterministic agent for deployment practice; no real LLM key needed."""

    def answer(self, question: str) -> AgentResponse:
        normalized = question.lower()
        hits = []
        for key, snippet in KNOWLEDGE_BASE.items():
            if key in normalized or re.search(rf"\b{key}\b", normalized):
                hits.append((key, snippet))
        if not hits:
            hits = [
                ("cloud", KNOWLEDGE_BASE["cloud"]),
                ("docker", KNOWLEDGE_BASE["docker"]),
                ("security", KNOWLEDGE_BASE["security"]),
            ]
        answer = "\n".join(f"- {snippet}" for _, snippet in hits[:4])
        answer += "\n\nGợi ý triển khai: kiểm tra /health, /ready, X-API-Key, biến PORT và structured logs trước khi deploy."
        citations = [f"mock_kb:{key}" for key, _ in hits[:4]]
        return AgentResponse(answer=answer, citations=citations, tokens_estimated=estimate_tokens(question + answer))
