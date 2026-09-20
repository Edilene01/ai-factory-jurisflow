# Registros de decisão arquitetural

Cada arquivo aqui documenta uma decisão, no formato MADR. O que se registra é o *porquê* da
escolha, com as alternativas que foram descartadas e as consequências, inclusive as ruins.
Instrução de instalação e comando de terminal não entram em ADR: isso é assunto do README.

| ADR | Decisão | Status | Data |
|---|---|---|---|
| [ADR-001](ADR-001-manter-n8n-como-orquestrador.md) | Manter o n8n como orquestrador e evoluir o protótipo | Aceita | 18/09/2026 |
| [ADR-002](ADR-002-hospedagem-railway-ambientes-separados.md) | Hospedar em Railway, com dev e prod separados | Aceita | 18/09/2026 |

Uma ADR aceita não é imutável. Quando a realidade mudar, cria-se uma nova ADR que substitui
a anterior, e a antiga passa a `status: substituída`, sem ser apagada, porque o histórico da
decisão é parte do valor do registro.
