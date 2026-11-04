# 🤖 Diretrizes e Governança Global de Desenvolvimento - PROJETOS IA

Este arquivo estabelece os padrões arquiteturais, de segurança máxima em camadas, proteção de segredos, gestão documental e governança para **todas as aplicações e sistemas** construídos neste ecossistema.

---

## 1. 📋 Planejamento, Alinhamento e Diálogo com o Usuário
- **Apresentação Prévia Obrigatória:** Antes de iniciar qualquer desenvolvimento, refatoração ou criação de módulo, o Agente **deve obrigatoriamente conversar com o usuário**, apresentando:
  - **Escopo e Objetivo:** O que será construído e o problema que será resolvido;
  - **Pilha e Ferramentas:** As ferramentas, bibliotecas, pacotes e componentes exatos que serão empregados;
  - **Modelos e Estruturas de Interface:** Sugestão prévia dos melhores modelos de componentes e layouts modernos do ecossistema React para validação visual;
  - **Fluxo Arquitetural e de Segurança:** Como as partes (frontend, backend, banco e provedores de IA) irão se comunicar, permitindo validação prévia pelo usuário.

---

## 2. 🛡️ Segurança Máxima, Proteção de Chaves de IA e Governança de Documentos (Padrão Google / Zero Trust)

### A. Proteção Estrita e Blindagem de API Keys e Segredos
- **Tolerância Zero a Segredos em Código:** É terminantemente proibido inserir senhas, tokens JWT, credenciais de banco ou chaves de API (*API Keys* de OpenAI/GPT, Claude/Anthropic, Google Gemini, Groq, etc.) diretamente no código-fonte (*hardcoded*), em comentários, em logs ou em páginas/scripts do frontend.
- **Backend como Proxy Seguro Exclusivo:** O frontend **NUNCA** acessa APIs de IA ou serviços confidenciais diretamente. Toda comunicação com provedores externos deve ser intermediada pelo Backend (Python/FastAPI), que injeta as credenciais a partir do ambiente do servidor.
- **Gestão Rigorosa de Variáveis de Ambiente (`.env`):**
  - Armazenamento local de credenciais exclusivamente em arquivos `.env`.
  - O arquivo `.env` deve constar obrigatoriamente no topo do `.gitignore` de todos os projetos.
  - Disponibilizar apenas um `.env.example` contendo as chaves sem valores confidenciais.
- **Sanitização de Logs (Redaction):** Proibido imprimir chaves de API, senhas ou dados sensíveis em logs de console (`print`, `logger`), mensagens de erro ou retornos de exceção para o usuário.

### B. Proteção Máxima de Documentos e Arquivos Anexados
- **Isolamento Fora da Raiz Pública:** Diretórios de upload e arquivos anexados nunca devem ficar expostos como diretórios estáticos públicos da web.
- **Prevenção contra Path Traversal e Injeções:** 
  - Todo nome de arquivo deve ser sanitizado e renomeado com identificadores únicos seguros (ex.: `UUIDv4`) no armazenamento.
  - Validação rigorosa de tipo MIME real e extensão permitida antes do processamento.
- **Acesso Controlado e Links Temporários:** Acesso a documentos restrito a usuários autenticados, com uso de URLs temporárias e assinadas (*Signed URLs*) com tempo de expiração curto quando aplicável.
- **Limpeza Segura de Arquivos Temporários:** Arquivos temporários criados para processamento em memória ou disco devem ser excluídos com blocos `try...finally` logo após a execução.
- **Criptografia e Integridade:** Dados sensíveis em repouso e em trânsito devem seguir padrões criptográficos modernos (TLS/HTTPS e Row Level Security - RLS).

### C. Arquitetura de Defesa em Camadas (Defense-in-Depth)
- **Validação Estrita de Entrada:** Toda requisição no backend deve ser tipada, inspecionada e validada via Pydantic para neutralizar injeções de dados e inconsistências.
- **Controle de Acesso Baseado em Perfis (RBAC):** Estrutura preparada para autorização granular por papéis, garantindo que nenhum usuário acerte endpoints ou documentos sem permissão expressa.
- **CORS e Headers de Segurança:** Configuração segura de origens permitidas (CORS) e inclusão de headers de proteção contra vulnerabilidades web modernas (OWASP Top 10).

### D. Isolamento e Blindagem contra Injeção de Prompt e Envenenamento de Contexto (Ken Huang & Chris Hughes)
- **Triagem de Barreira de Proteção em Tempo Real (Guardrails):** Todos os documentos, planilhas ou textos recuperados/ingeridos para contexto de IA/RAG devem passar por sanitização antes de serem injetados no contexto de trabalho.
- **Saneamento Ativo de Texto Recuperado:** Neutralização e remoção de tentativas de substituição de prompt do sistema (*system prompt override*), instruções ocultas (*ignore previous instructions*), caracteres de controle maliciosos e sequências de tokens não autorizadas.
- **Encapsulamento Criptográfico e Tags Seguras:** Passagens de texto recuperadas devem ser estritamente encapsuladas dentro de delimitadores seguros (ex.: `<untrusted_content hash="...">...</untrusted_content>`), acompanhados de hash de integridade criptográfica.
- **Imposição de Instruções Estritas de Sistema:** O prompt do sistema deve instruir o modelo a tratar todo conteúdo encapsulado estritamente como **dados passivos não confiáveis para análise**, e nunca como comandos operacionais executáveis.


---

## 3. 🚀 Pilha Tecnológica Padrão (Full-Stack de Alta Performance)

### A. Frontend (Interface Visual, Modelos Modernos e Experiência do Usuário)
- **Framework Principal:** **React 18+** com **TypeScript** obrigatório (`.tsx` / `tsconfig.json`).
- **Aproveitamento dos Melhores Modelos React:** Utilização de padrões e modelos consolidados do ecossistema React (ex.: componentes acessíveis no estilo Shadcn UI, Radix UI, Framer Motion para micro-animações suaves e bibliotecas modernas de dashboards), garantindo interfaces ricas, intuitivas e de alto padrão visual.
- **Motores de Execução:**
  - **Vite:** Padrão para ferramentas operacionais, painéis, sistemas internos e processamento (velocidade instantânea e leveza).
  - **Next.js:** Padrão para portais públicos, plataformas abertas e landing pages com SEO.
- **Design System & Estilização:** **TailwindCSS** + **Lucide React** (interface limpa, moderna, responsiva e com identidade visual unificada).
- **Comunicação:** **Axios** para consumo padronizado das APIs do backend.

### B. Backend (Motor de Processamento e APIs)
- **Linguagem:** **Python 3.10+**.
- **Framework de API:** **FastAPI** + **Uvicorn** + **Pydantic** (performance assíncrona e validação estrita).
- **Processamento de Dados:** Engenharia de alta performance e resiliência para ingestão, transformação e exportação de dados massivos em múltiplos formatos.

### C. Persistência e Banco de Dados
- **Banco em Nuvem:** **Supabase (PostgreSQL)** com Row Level Security (RLS) e políticas de isolamento de dados.
- **Armazenamento Local / Cache:** SQLite ou armazenamento de sessão.

---

## 4. ⚡ Automação de Inicialização (Zero Esforço para o Usuário)
- Todo projeto que possua frontend e/ou backend deve conter o script **iniciar_app.bat**.
- **Automação Inteligente:**
  1. Detectar se `frontend/node_modules/` existe; se ausente, executar `npm install` automaticamente.
  2. Detectar se as dependências Python estão instaladas; se ausentes, executar `pip install -r requirements.txt`.
  3. Iniciar os servidores e abrir o navegador automaticamente na porta correta.

---

## 5. 🎨 Identidade Visual, Preservação e Boas Práticas
- **Preservação de Layout:** Nunca alterar a posição de botões, paleta de cores ou a disposição das telas sem alinhamento e autorização explícita do usuário.
- **Componentização Modular:** Construir telas divididas em componentes reutilizáveis, pequenos e de responsabilidade única.
- **Edições Cirúrgicas:** Alterar estritamente o trecho de código necessário para corrigir ou adicionar funções, evitando reescritas desnecessárias.
- **Idioma e Comunicação:** Respostas, explicações e documentações sempre em **Português do Brasil**, utilizando linguagem clara e acessível após termos técnicos.

---

## 6. 🧠 Observabilidade Ativa e Auto-Evolução das Diretrizes (Melhoria Contínua)
- **Agente como Guardião e Observador Ativo:** O Agente deve monitorar continuamente todas as tarefas, alterações, novos requisitos e fluxos propostos pelo usuário no dia a dia.
- **Detecção de Oportunidades e Novas Necessidades:** Sempre que uma solicitação do usuário evidenciar:
  1. A necessidade de **segurança redobrada** além dos padrões atuais;
  2. Uma **nova ferramenta, biblioteca ou padrão arquitetural** que melhore significativamente a performance, robustez ou usabilidade do ecossistema;
  3. Um **novo aprendizado ou padrão de excelência** que deva ser compartilhado com todos os projetos.
- **Protocolo de Atualização Pró-Ativa com Alerta ao Usuário:**
  - O Agente **NUNCA** altera as regras silenciosamente.
  - O Agente deve **despertar imediatamente, alertar o usuário e explicar em linguagem simples** o que foi identificado, o porquê aquela melhoria é vantajosa e solicitar a autorização para atualizar o `AGENTS.md`.
  - Após a aprovação do usuário, o Agente consolida a nova diretriz globalmente, garantindo a evolução perpétua e segura de todo o ecossistema.

---

## 7. 🛡️ Protocolo Obrigatório de Teste e Homologação Prévia (Ambiente Seguro antes da Produção)

- **Tolerância Zero a Código não Homologado em Produção:** Qualquer alteração, correção ou nova funcionalidade solicitada deve ser obrigatoriamente testada e validada em ambiente seguro (sandbox de testes/homologação) antes de ser integrada e liberada para o ambiente produtivo.
- **Camada de Testes Automatizados (Pytest & TestClient):**
  - Manter uma suíte de testes de validação no diretório `backend/tests/`.
  - Antes de concluir qualquer tarefa de código, o Agente deve executar os testes automatizados para verificar a integridade das rotas, integridade dos cálculos contábeis e ausência de regressões (*efeitos colaterais indesejados*).
- **Isolamento de Estado (Sandbox de Dados):**
  - Os testes devem ser executados em memória ou com dados simulados (*fixtures*), sem contaminar, sobrescrever ou alterar arquivos e bancos de produção.
- **Confirmação e Transparência:**
  - O Agente deve reportar o resultado da validação com clareza ao usuário (ex.: quais testes foram executados e seu status), confirmando que a alteração está segura e pronta para uso.

