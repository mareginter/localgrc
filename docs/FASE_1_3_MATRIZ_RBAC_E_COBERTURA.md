# Fase 1.3 — Auditoria RBAC das views

## Âmbito desta entrega

Esta etapa acrescenta uma bateria de regressão que percorre os endpoints de escrita identificados nas aplicações Core, Risks, Controls, Policies, Audits, Incidents, Vendors, Evidence, Vulnerabilities, Library e Assistant.

O teste usa um utilizador com o papel `reader` e uma associação ativa à organização. Cada endpoint de mutação é invocado por POST e tem de responder HTTP 403 antes de processar o conteúdo ou procurar o objeto-alvo. Para endpoints com identificador, usa-se um UUID deliberadamente inexistente: a autorização tem de ser avaliada antes da consulta ao objeto.

## Inventário observado na versão v2

| Área | Leitura | Escrita observada | Papel exigido nas views |
|---|---|---|---|
| Riscos e ativos | utilizador autenticado com associação | criação/edição, avaliações e tratamentos | admin, risk_manager, contributor |
| Controlos | utilizador autenticado com associação | criação/edição, ligações, implementações e transições | admin, control_owner, contributor |
| Políticas | utilizador autenticado com associação | criação/edição, versões, aprovação e transições | admin, risk_manager |
| Auditorias e constatações | utilizador autenticado com associação | criação/edição, transições, ações corretivas/verificação | admin, auditor |
| Incidentes | utilizador autenticado com associação | criação/edição, transições, prazos e ligações | admin, risk_manager, contributor |
| Fornecedores | utilizador autenticado com associação | criação/edição, avaliações, ligações e transições | admin, risk_manager, contributor |
| Evidências | utilizador autenticado com associação | criação/edição/verificação | admin, control_owner, contributor |
| Vulnerabilidades | utilizador autenticado com associação | criação/edição | admin |
| Biblioteca de templates | utilizador autenticado com associação | carregamento | admin |
| Assistente | utilizador autenticado com associação | upload de documentos RAG | admin |
| Utilizadores | admin | criação/edição | admin |
| Frameworks/requisitos | utilizador autenticado com associação | sem endpoints de escrita identificados | leitura |

## Interpretação e limitações

- `reader` deve ser estritamente de leitura; a bateria verifica a negação de POST nos endpoints de escrita inventariados.
- A existência de `@login_required` numa view GET não significa, por si só, falha RBAC: é necessário distinguir operações de consulta de operações de alteração.
- Esta bateria não prova que cada papel autorizado tem exatamente os privilégios funcionais pretendidos. Essa validação positiva exige uma matriz de negócio aprovada e testes por papel/ação.
- Não foram identificados endpoints HTTP de eliminação nas rotas das aplicações revistas. É necessário verificar também o Django Admin, tarefas assíncronas e eventuais endpoints fora dos `urls.py` das aplicações.
- A autorização de leitura e os downloads devem continuar a ser verificados separadamente quanto à associação à organização e ao objeto concreto.
- Não foram alterados modelos, dados, migrações ou permissões de utilizadores nesta etapa.


## Correção de interface de autenticação — modal

A página de autenticação foi convertida numa janela modal acessível (`role=dialog`, `aria-modal=true`), com apresentação responsiva, mensagens de erro e preservação do parâmetro `next` para regressar ao destino solicitado após autenticação. O conteúdo protegido do dashboard não é exposto a utilizadores anónimos; o fundo apresenta apenas uma composição visual ilustrativa. Foram acrescentados testes de renderização, autenticação/redirect e credenciais inválidas.


## Correção complementar — terminar sessão

A barra de navegação comum (`risks/base_risks.html`) apresenta agora a identidade do utilizador autenticado e um botão **Terminar sessão**. A saída é submetida por POST com token CSRF, conforme o comportamento do Django 5.x. Após terminar sessão, o utilizador é encaminhado para `/login/`. Foram adicionados dois testes: presença do controlo na navegação autenticada e encerramento efetivo da sessão.
