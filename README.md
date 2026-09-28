# Demonstração — Consulta de opção pelo Simples Nacional

> Projeto de portfólio de **Victória Pedrosa**. **Demonstração** de consulta de opção pelo Simples Nacional — versão com dados fictícios (nomes, CNPJs, e-mails e IDs internos substituídos).

## Problema de negócio
Confirmar a opção pelo Simples Nacional de cada empresa exigia consulta individual.

## Antes x depois
| | Antes | Depois |
|---|---|---|
| Como é feito | Consulta manual no portal. | Robô consulta e organiza os comprovantes em PDF. |

## Ganho
- Comprovação em lote da opção pelo SN.

## Tecnologias
Python, SQLite, pandas

## Arquivos
- `automacao_sn.py`
- `requirements.txt`

## Como rodar
1. `pip install -r requirements.txt`
2. Copie `.env.exemplo` para `.env` e preencha os caminhos.
3. Execute o script principal.

## Autora
Victória Pedrosa — Product Owner do Time de IA, automação de processos contábeis e fiscais.
