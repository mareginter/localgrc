# LocalGRC — Fase 1.2: Isolamento organizacional e RBAC inicial

## Âmbito

Esta entrega introduz uma resolução central da organização ativa e aplica isolamento organizacional aos módulos web existentes. Também introduz verificações de função nas operações de escrita mais sensíveis.

## Alterações

- Criado `apps.core.access` para resolver a organização ativa exclusivamente através de associações `UserRole` não eliminadas.
- Adicionado seletor de organização na barra superior, com alteração apenas por POST e validação de pertença.
- Removidas as resoluções `Organization.objects.first()` das vistas dos módulos operacionais.
- Aplicadas permissões por função nas operações de escrita de riscos, controlos, evidências, auditorias, incidentes, políticas e fornecedores.
- Gestão de utilizadores limitada à organização ativa; novos utilizadores recebem inicialmente a função `contributor` nessa organização.
- Acesso ao Django Admin global limitado a superutilizadores de plataforma.
- Consultas de requisitos/frameworks e registos de vulnerabilidades limitadas à organização ativa.
- Adicionado isolamento organizacional aos documentos RAG e à pesquisa de contexto do assistente.
- Adicionado isolamento à biblioteca de modelos documentais.
- Criado `TenantScopedModelFormMixin` para limitar escolhas de utilizadores, riscos, ativos, controlos, fornecedores e requisitos à organização ativa.
- A associação de evidências valida o objeto de destino e a organização, sem revelar se um UUID existe noutra organização.
- Comando de seed de controlos exige agora o slug explícito da organização.
- A pesquisa RAG do assistente filtra os documentos pela organização ativa; o endpoint de chat é POST-only e permanece protegido pelo middleware CSRF do Django.
- Os downloads de evidências e versões de políticas passam por views Django que validam a organização e emitem `X-Accel-Redirect`; o Nginx mantém `/uploads/` como localização `internal`.
- Os helpers de workflow distinguem leitura e criação: os pedidos GET não criam `WorkflowInstance`; a criação ocorre no POST de transição.
- As transições validam a associação do estado e do objeto à definição e organização corretas, exigem associação ativa do utilizador à organização, aplicam `requires_comment` e gravam o estado e o `AuditLog` na mesma transação.
- O superutilizador de plataforma pode contornar a função exigida numa transição, mas não a pertença à organização nem as validações de integridade.
- Os formulários de criação/alteração de utilizadores e o bootstrap aplicam os validadores de password configurados no Django. O Compose deixou de fornecer uma password administrativa predefinida e deixou de usar `*` como valor por omissão de `ALLOWED_HOSTS`.
- O pacote de entrega desta revisão exclui `.env` e `backups/`; estes ficheiros permanecem intocados na instalação original.

## Matriz inicial de permissões de escrita

| Módulo | Funções autorizadas |
|---|---|
| Riscos e ativos | admin, risk_manager, contributor |
| Controlos | admin, control_owner, contributor |
| Evidências | admin, control_owner, contributor |
| Auditorias e constatações | admin, auditor |
| Incidentes | admin, risk_manager, contributor |
| Políticas | admin, risk_manager |
| Fornecedores | admin, risk_manager, contributor |
| Upload de conhecimento IA | admin |
| Gestão de vulnerabilidades | admin |
| Gestão de modelos na biblioteca | admin |
| Gestão de utilizadores | admin |

A matriz é uma política inicial conservadora e deve ser validada com os responsáveis funcionais antes de produção. A função `reader` permanece apenas de consulta.

## Migrações

Foram adicionadas migrações para os campos organizacionais de vulnerabilidades, documentos do assistente e modelos da biblioteca. Os registos antigos são associados automaticamente à organização existente apenas quando existe exatamente uma organização ativa. Se existirem várias organizações, os registos legados permanecem sem organização e não são apresentados a nenhum tenant; devem ser revistos e atribuídos manualmente antes de serem reativados.

### Atualização de uma instalação existente

1. Fazer backup verificado da base de dados e dos uploads.
2. Rever o plano de migrações:

```bash
docker compose exec app python manage.py migrate --plan
```

3. Em instalações antigas onde as tabelas das apps `assistant`, `library` e `vulnerabilities` já tenham sido criadas sem histórico de migrações, aplicar o reconhecimento inicial:

```bash
docker compose exec app python manage.py migrate --fake-initial
```

4. Executar as migrações pendentes:

```bash
docker compose exec app python manage.py migrate
```

5. Validar a aplicação e os testes:

```bash
docker compose exec app python manage.py check
docker compose exec app pytest -q
```

Não executar migrações numa instalação de produção sem backup e validação prévia do plano.

## Limitações conhecidas / trabalho pendente

- A matriz RBAC é aplicada às operações de escrita identificadas. Foram acrescentados testes negativos a 12 endpoints de criação para o papel `reader`; falta completar a cobertura de todas as operações de alteração, eliminação e ações específicas de cada módulo.
- A correção dos downloads cobre evidências e versões de políticas. Outros tipos de ficheiros devem ser revistos antes de serem expostos por novas ligações de download.
- O RAG está filtrado por organização, mas a pesquisa de similaridade continua a percorrer os chunks em Python; `pgvector` ou outra indexação vetorial é uma evolução necessária quando o volume crescer. Convém acrescentar um teste explícito de não divulgação entre organizações.
- O login continua sem rate limiting e o campo `totp_secret` não corresponde a uma implementação funcional de MFA/2FA.
- HSTS e redirecionamento HTTPS são configuráveis, mas dependem de uma terminação TLS real e de configuração operacional do proxy. Não ativar HSTS na configuração HTTP local atual.
- Os backups continuam sem cifragem e são armazenados no host; devem ser cifrados e copiados para uma localização externa protegida.
- As dependências Python e a imagem `ollama/ollama:latest` ainda não estão totalmente fixadas por versões/digests, pelo que as builds não são totalmente reproduzíveis.
- O Django Admin continua a ser uma superfície global para superutilizadores de plataforma; deve ser tratado como acesso break-glass.
- Dados legados em organizações múltiplas podem permanecer com `organization=NULL` até classificação manual.
- Não foi possível executar testes Django nesta estação de análise porque Django/PostgreSQL/Docker não estão instalados e o ambiente não dispõe de acesso à Internet para instalar as dependências. `python -m compileall -q backend` e a validação YAML do `docker-compose.yml` passaram; estes controlos estáticos não substituem `manage.py check`, migrações reais ou testes de integração.

## Comandos de dados de exemplo

Os comandos de seed que anteriormente escolhiam implicitamente a primeira organização exigem agora o slug explícito:

```bash
python manage.py seed_sample_controls --organization default
python manage.py seed_templates --organization default
python manage.py test_vulns --organization default
```

Substituir `default` pelo slug real da organização pretendida.
