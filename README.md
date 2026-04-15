#Em manutenção.

# Modpack AI (Forge)

Aplicacao local em Python 3.11+ com GUI Tkinter para gerar listas de mods Forge com foco em estabilidade.

## Requisitos

- Python 3.11+
- `requests`

Instalacao:

```bash
pip install requests
```

## Execucao

No diretorio `modpack_ai`:

```bash
python main.py
```

## Estrutura

- `main.py`: ponto de entrada
- `gui.py`: interface Tkinter
- `core/api_client.py`: integracao Modrinth/GitHub
- `core/cache_manager.py`: cache SQLite (`data/cache.db`)
- `core/mod_analyzer.py`: classificacao tecnica e metadados
- `core/scoring_system.py`: score individual e score geral
- `core/compatibility_engine.py`: selecao de mods e dependencias
- `core/pack_generator.py`: orquestracao do fluxo

## Exportacao

A GUI permite salvar o resultado em:

- `.txt`
- `.json`

Os arquivos podem ser salvos em `exports/`.

## Observacoes

- A API do GitHub sem token tem rate limit baixo. Opcionalmente defina `GITHUB_TOKEN` no ambiente.
- O sistema usa heuristicas; sempre valide o pack final em ambiente de teste.
