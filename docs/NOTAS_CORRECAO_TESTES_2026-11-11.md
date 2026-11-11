# LocalGRC — correção dos testes (11-11-2026)

## Correções desta revisão

- O snapshot de auditoria continua a guardar todos os campos, incluindo `updated_at`.
- O `diff` ignora campos `auto_now`, para que uma atualização automática de timestamp não seja confundida com uma alteração funcional.
- Os fixtures partilhados `org` e `user` passaram a existir no nível raiz do backend, ficando acessíveis aos testes de todos os módulos. O fixture local de `core` foi mantido para compatibilidade.

## Testes

Executar no container de desenvolvimento:

```powershell
docker compose run --rm app sh -c "python -m pip install --user -e '.[dev]' && python -m pytest"
```

A execução anterior reportou 46 testes aprovados, 2 falhas na auditoria e 6 erros por ausência de fixtures. Esta revisão corrige diretamente essas duas causas. A suite ainda precisa de ser executada no ambiente Docker do projeto para confirmar o resultado integral; não é declarado aqui qualquer resultado de execução que não tenha ocorrido.
