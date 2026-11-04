---
name: rag-security
description: Padrões de isolamento criptográfico, guardrails de tempo real e saneamento ativo contra injeção de prompt e envenenamento de contexto em agentes e sistemas de RAG corporativos (Ken Huang & Chris Hughes).
---

# 🛡️ Skill: Isolamento Criptográfico e Segurança de RAG / Contexto de IA (Ken Huang & Chris Hughes)

Esta habilidade (Skill) estabelece os procedimentos técnicos e padrões de implementação para neutralizar ataques de **Injeção de Prompt (*Prompt Injection*)** e **Envenenamento de Contexto (*Context Poisoning*)** em documentos, planilhas e passagens recuperadas.

---

## 🎯 1. Fundamentos da Arquitetura Segura

Documentos externos (PDFs, balancetes, planilhas Excel, dados de RAG) são considerados **fontes de dados não confiáveis**. 
Para evitar que atacantes insiram comandos ocultos como `ignore previous instructions` ou `system prompt override` no meio de textos legítimos, a arquitetura deve aplicar o **princípio do isolamento criptográfico**.

### Pilares de Proteção:
1. **Triagem de Barreira de Proteção em Tempo Real (*Guardrails*):** Interceptação do texto antes de qualquer injeção no contexto do modelo.
2. **Saneamento Ativo:** Remoção de padrões de injeção, caracteres nulos e sequências de tokens não autorizadas (ex.: `<|im_start|>`, `[INST]`).
3. **Encapsulamento Criptográfico:** Inclusão do conteúdo dentro de tags delimitadoras estritas com hash de integridade SHA-256 (`<untrusted_content sha256="...">`).
4. **Instruções Estritas de Nível de Sistema:** Forçar o modelo a tratar o texto encapsulado como **dados inertes para leitura e análise**, e nunca como instruções operacionais.

---

## 💻 2. Implementação de Referência (Python)

Utilizar o serviço corporativo localizado em `backend/app/services/security_guardrails.py`:

```python
from app.services.security_guardrails import guardrails_seguranca

# 1. Recupera o texto de um documento ou planilha
texto_documento = extrair_texto_planilha(arquivo)

# 2. Aplica saneamento e isolamento criptográfico
resultado_seguro = guardrails_seguranca.encapsular_em_tags_seguras(
    texto=texto_documento,
    identificador_origem="demonstracao_contabil_upload"
)

# 3. Monta o contexto protegido para o modelo de IA
contexto_ia = f"{resultado_seguro['instrucao_sistema']}\n\n{resultado_seguro['bloco_seguro']}"
```

---

## 🧪 3. Validação e Testes Obrigatórios

Toda alteração que envolva processamento de documentos deve conter testes que comprovem:
- Interceptação de tentativas de injeção;
- Integridade do hash SHA-256;
- Execução segura dos testes via `pytest tests/test_sistema_seguro.py`.

