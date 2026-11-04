---
name: langgraph-cognitive
description: Padrões de arquitetura cognitiva com LangGraph, Context Engineering, Raw Memory, Checkpointers e Sumarização Progressiva para agentes de IA financeiros (Lion Labs / 2026).
---

# 🧠 Skill: Arquitetura Cognitiva com LangGraph & Memória Multi-Camadas (2026)

Esta habilidade (Skill) padroniza a implementação de agentes cognitivos persistentes utilizando **LangGraph**, aplicando os princípios modernos de **Engenharia de Contexto (*Context Engineering*)** para eliminar a perda de contexto (*Lost in the Middle*) e viabilizar memórias de curto, médio e longo prazo.

---

## 🎯 1. Fundamentos da Memória em 3 Camadas

1. **Curto Prazo (Working Memory):** Buffer recente das últimas interações literais (`add_messages`).
2. **Médio Prazo (Threads & Checkpointers):** Persistência de sessões via `MemorySaver` ou `SqliteSaver` indexados por `thread_id`.
3. **Longo Prazo (Memória Episódica):** Fatos, decisões de governança e metas estratégicas gravadas em lista imutável no estado.
4. **Sumarização Progressiva Ativa:** Condensação periódica de mensagens antigas quando o volume ultrapassa o limiar, evitando degradação de precisão.

---

## 💻 2. Padrão de Estado Estruturado (Raw Memory)

```python
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class EstadoAgenteFinanceiro(TypedDict):
    mensagens: Annotated[List[BaseMessage], add_messages]
    sumario_conversa: str
    fatos_estrategicos: List[str]
    ano_ativo: str
    trimestre_ativo: str
    insight_jev: Optional[Dict[str, Any]]
```

---

## 🛡️ 3. Integração com Guardrails
Toda mensagem antes de entrar no grafo deve ser sanitizada pelo serviço:
```python
from app.services.security_guardrails import guardrails_seguranca

texto_sanitizado, ameaca = guardrails_seguranca.sanitizar_texto(mensagem_bruta)
```

