# LocalGRC — Fase 1.1: Auditoria inicial de segurança

Data: 10/11/2026  
Estado: auditoria inicial concluída; correções parciais aplicadas; fase de segurança ainda aberta.

## Âmbito analisado

- Configuração Django e middleware.
- Autenticação, modelo de utilizador e atribuição de funções.
- Resolução de organização nos módulos.
- Endpoints do assistente e processamento RAG.
- Módulo de vulnerabilidades.
- Processo de backup e configuração Docker/Nginx.
- Estrutura de testes existente.

## Correções aplicadas nesta entrega

1. A chave `DJANGO_SECRET_KEY` deixa de ter um valor de fallback conhecido e passa a ser obrigatória, com pelo menos 50 caracteres.
2. `DJANGO_ALLOWED_HOSTS` passa a ter uma lista local restrita por defeito. Wildcard é rejeitado quando `DEBUG=False`.
3. Foram adicionadas opções explícitas para cookies seguros, redirecionamento HTTPS e HSTS. A ativação de HSTS com `DEBUG=True` é rejeitada.
4. O endpoint de streaming do assistente deixou de estar isento de CSRF e passou a aceitar apenas POST.
5. O endpoint do assistente valida JSON, tamanho da pergunta, número de mensagens e papéis permitidos no histórico. Erros internos deixam de ser devolvidos diretamente ao cliente.
6. Upload de PDF passou a exigir POST, limite de 20 MB, extensão PDF e assinatura `%PDF-`; erros internos são registados no servidor.
7. O backup passou a criar conjuntos versionados, validar o dump com `pg_restore --list` e o arquivo de uploads com `tar -tzf`, e só publica o conjunto depois das validações.
8. A retenção passa a manter os sete conjuntos completos mais recentes.

## Achados ainda por resolver — prioridade crítica

### 1. Isolamento organizacional incompleto

Vários módulos resolvem a organização com `Organization.objects.first()` através de funções `_org(request)`. Isto não representa a organização a que o utilizador pertence e não é seguro para multiempresa.

Módulos identificados: Core/Dashboard, Risks, Frameworks, Controls, Policies, Audits, Vendors, Incidents e Evidence. O módulo Audits também resolve a primeira organização dentro da função de workflow.

**Ação necessária:** criar serviço central de organização ativa, baseado em `UserRole`, seleção explícita quando existirem várias organizações e testes negativos de isolamento entre empresas. A migração deve incluir inventário dos utilizadores existentes sem associação, sem lhes atribuir permissões administrativas automaticamente.

### 2. RBAC não aplicado de forma transversal

A maioria das vistas dos módulos está protegida apenas por `login_required`. A existência de `Role` e `UserRole` não significa que as permissões estejam aplicadas. A gestão de utilizadores usa `is_staff`/`is_superuser`, não um modelo coerente de permissões por organização.

O modelo `WorkflowInstance.can_transition()` também permite a transição a qualquer utilizador autenticado quando a transição não tem `required_role` definido; a verificação de associação à organização não é geral.

**Ação necessária:** matriz de permissões por função, organização, módulo e operação; decoradores/serviços comuns; testes de acesso permitido e negado.

### 3. Módulo de vulnerabilidades sem organização

O modelo `Vulnerability` não tem campo `organization`. As vistas listam, consultam, criam e alteram registos globalmente. Isto constitui um risco direto de exposição de dados entre organizações.

**Ação necessária:** migração aditiva, associação controlada dos registos existentes, filtragem por organização em todas as vistas e testes de isolamento.

### 4. RAG sem isolamento organizacional

`Document` e `DocumentChunk` não têm associação a organização nem a utilizador. `rag.search_context()` consulta todos os chunks. Assim, os documentos de conhecimento não estão isolados por organização.

**Ação necessária:** associar documentos e chunks a uma organização, aplicar filtragem no retrieval e validar acesso a documentos. Fazer migração de dados com plano explícito para os documentos existentes.

## Achados importantes adicionais

- `Frameworks.requirement_detail` consulta o requisito apenas pelo identificador, sem filtrar a organização através da versão/framework.
- O upload de evidências e outros anexos precisa de validação uniforme de tamanho, tipo real, nome, armazenamento e autorização.
- `assistant_health` responde `ok` sem testar efetivamente a disponibilidade do serviço Ollama.
- O script de backup anterior não usava `set -e` nem verificava o resultado do `pg_dump`; podia anunciar sucesso apesar de um dump vazio.
- O Nginx disponibiliza `/uploads/` como `internal`, o que é uma boa proteção contra acesso direto, mas os downloads devem continuar a passar por vistas que validem a autorização.
- O Docker Compose usa tags de imagem que devem ser fixadas a versões/digests aprovados num ciclo de hardening posterior.

## Testes e limitações desta entrega

- `python -m compileall -q backend`: passou (sintaxe Python).
- `sh -n deploy/backup.sh`: passou (sintaxe shell).
- Teste de integração do backup com comandos PostgreSQL simulados: passou; criou dump, arquivo, manifesto e conjunto final.
- A suite pytest não pôde ser executada neste ambiente: Django não está instalado e Docker não está disponível. Não considerar os testes funcionais aprovados.

## Configuração obrigatória antes de arrancar

O `.env` usado na análise continha `DJANGO_ALLOWED_HOSTS=*`. Como o código agora rejeita wildcard com `DEBUG=False`, alterar essa variável no `.env` para os hosts efetivamente usados, por exemplo `localhost,127.0.0.1` para acesso local. Se existir acesso por IP ou domínio, acrescentá-lo explicitamente. Não copiar o `.env` para partilhas ou repositórios.

A password PostgreSQL encontrada no `.env` tinha apenas seis caracteres. Deve ser substituída por uma password aleatória forte (recomendo pelo menos 20 caracteres) e atualizada de forma coordenada na configuração do PostgreSQL. Não reutilizar a password administrativa.

Definir `DJANGO_SESSION_COOKIE_SECURE=true` e `DJANGO_CSRF_COOKIE_SECURE=true` quando a aplicação estiver servida exclusivamente por HTTPS. Configurar HSTS apenas depois de confirmar HTTPS em todos os caminhos e subdomínios relevantes.

## Próximo bloco de trabalho

1. Implementar organização ativa central baseada em `UserRole`.
2. Criar fluxo de seleção de organização para utilizadores com várias associações.
3. Migrar e filtrar o módulo de vulnerabilidades.
4. Migrar documentos RAG para isolamento por organização.
5. Aplicar RBAC transversal e fechar as falhas em workflows.
6. Criar testes de isolamento multiempresa e autorização antes de avançar para o restante hardening.
