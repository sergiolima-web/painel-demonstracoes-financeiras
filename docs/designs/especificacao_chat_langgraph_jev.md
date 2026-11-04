# 📋 Especificação Técnica: Chatbot Executivo com LangGraph, Memória Multi-Camadas e JEV Engine

**Autor (O Elefante):** Sessão Principal de Arquitetura  
**Protocolo:** Elephant-Goldfish Model (EGM) + TypeSafe JEV  
**Data:** 2026-11-03  
**Status:** Em Revisão pelo Subagente Auditor Goldfish  

---

## 1. 🎯 Objetivo e Escopo
Integrar na interface visual do Painel de Balanço e DRE um **Widget de Chat Executivo Flutuante** (React 18 + TailwindCSS + Lucide Icons) conectado ao motor **LangGraph** e **TypeSafe JEV** do backend FastAPI (`POST /api/chat/agente-financeiro`).

### O que o sistema deve fazer:
1. Permitir que o acionista envie perguntas em linguagem natural sobre as demonstrações financeiras carregadas (Balanço, DRE e Índices);
2. Preservar o layout atual do painel sem deslocar botões, tabelas ou gráficos existentes;
3. Exibir o badge **`⚡🧠 JEV Engine`** em respostas validadas pelo motor cognitivo;
4. Manter o histórico da conversa em sessão ativa (`thread_id`), com sumarização progressiva e gravação de metas estratégicas;
5. Aplicar barreira de proteção de entrada via `security_guardrails` (Ken Huang & Chris Hughes).

---

## 2. 🔌 Contrato de Interface e API (Backend FastAPI)

### Endpoint Consumido:
* **Rota:** `POST /api/chat/agente-financeiro`
* **Request Payload (Pydantic):**
  ```json
  {
    "mensagem": "Qual é a nossa liquidez corrente e a meta de ROE?",
    "thread_id": "sessao_acionista_local",
    "ano": "2026",
    "trimestre": "1T"
  }
  ```
* **Response Payload:**
  ```json
  {
    "resposta": "Texto estruturado da análise...",
    "sumario_ativo": "Resumo acumulado...",
    "fatos_registrados": ["Diretriz: ROE > 15%"],
    "total_mensagens_sessao": 4,
    "thread_id": "sessao_acionista_local",
    "badge_ia": "⚡🧠 LangGraph + JEV Engine"
  }
  ```

---

## 3. 🎨 Design do Componente Frontend (React & Tailwind)
* **Localização no Painel:** Botão flutuante no canto inferior direito (`fixed bottom-6 right-6 z-50`).
* **Estado Recolhido:** Ícone com badge pulsante `⚡🧠 Consultor IA`.
* **Estado Expandido:** Janela flutuante elegante (estilo Shadcn/Tailwind), contendo:
  - Cabeçalho com status online e badge `⚡🧠 JEV + LangGraph`;
  - Área de mensagens com rolagem automática e balões diferenciados (Acionista vs. Consultor IA);
  - Indicador visual de digitação / raciocínio;
  - Campo de entrada de texto com botão de envio e atalho para `Enter`.
* **Preservação Estrita de Layout:** O widget é puramente flutuante (*fixed overlay*), não alterando a largura, grid ou posição das tabelas corporativas.

---

## 4. 🛡️ Segurança e Governança (Zero Trust)
1. **Frontend Seguro:** Nenhuma chamada direta a provedores externos de IA. Todo tráfego passa exclusivamente pela rota `/api/chat/agente-financeiro`.
2. **Sanitização Ativa:** A mensagem é inspecionada contra tentativas de injeção de prompt antes do processamento.
3. **Fallback Determinístico:** Se a chave da TypeSafe ou provedor estiver offline, o agente responde utilizando as regras contábeis especialistas locais.

---

## 5. 🧪 Plano de Testes e Homologação
1. Teste de contrato da rota de chat (`test_agente_langgraph_chat_e_memoria_contexto`);
2. Teste de gravação de fatos estratégicos e sumarização progressiva (`test_agente_langgraph_memoria_longo_prazo_e_sumarizacao`);
3. Validação de ausência de quebra no frontend ao renderizar mensagens longas ou com caracteres especiais.

