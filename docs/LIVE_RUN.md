# Gravação real Jev — 100 células

Execução de 21 de setembro de 2026, semente 21, cenário de proteína com adjuvante. Projeto independente de Gut. Tecido circular de uma camada, diâmetro 173,2 μm, visualização 3D. Modelo retornado: `jev-1.13.0`.

## Resultado observado

- 89 rodadas completas: **44,5 horas simuladas**, de uma meta de 45 horas.
- **8.463 decisões individuais reais do Jev**, com observações e opções locais registradas.
- Centro germinativo estabelecido aos 1.350 minutos (22,5 h), com quatro fundadores. Ao final: **16 B de GC**, 6 Tfh e 7 células apresentando pMHC.
- 100 células vivas ao final; nenhuma divisão ou morte. Nenhuma célula de memória, plasmócito ou secreção de anticorpos nesta execução.
- Todos os 160 pacotes de antígeno permanecem contabilizados, inclusive os degradados.

Os relógios, proporções e critérios de GC são propostos e não calibrados. Este resultado não prevê o comportamento de um linfonodo humano. Rotas de divisão, memória e plasma existem no código e foram alcançadas por testes sintéticos, mas não devem ser atribuídas a esta gravação Jev.

## Consumo e parada

Foram feitas **447 tentativas HTTP**, sob teto de 450. Uma rodada completa adicional exigiria cinco chamadas; por isso a gravação permanece honestamente marcada como **parcial**. Não foram gastas as três chamadas restantes em uma rodada incompleta.

Uso informado pelo serviço: **14.237.357 tokens de entrada** e **294.834 de saída**. Pela tarifa de US$ 0,042 por milhão de tokens de entrada e saída gratuita mostrada na captura fornecida pelo usuário, o consumo conhecido estimado é **US$ 0,597968994**, aproximadamente **US$ 0,60**. Uma requisição HTTP 400 não informou uso; eventual cobrança dela não está incluída. O saldo atual da conta não foi consultado.

## Revisões do protocolo

1. Distribuições arredondadas a duas casas: normalização apenas dentro do limite de arredondamento, sem alterar a escolha. Dez decisões aplicadas têm esse ajuste documentado e preservam os valores originais.
2. HTTP 400: causa original não confirmada, pois a primeira versão não preservava o corpo do erro. O lote rejeitado era o maior; o formato de tabelas locais reduziu seu tamanho em 38%, sem perder informações. A retomada funcionou e agora os erros HTTP são registrados.
3. Na tentativa 369, Jev escolheu MOVE (0,42), embora WAIT tivesse 0,43. A resposta inteira foi rejeitada e preservada no histórico; após revisão explícita, apenas esse lote foi solicitado novamente.

Não houve repetição automática, decisão sintética substituta ou alteração retroativa de decisões. Respostas válidas já pagas foram reutilizadas nas retomadas. O formato v1 foi usado no início; v2 usa tabelas sem perda de informação. Essa mudança de formato é parte da proveniência da execução.

## Abrir e verificar

Com o servidor local ativo: [abrir a gravação](http://127.0.0.1:8010/?recording=940f891b6407c4a24371). Também está no menu **Saved Jev examples**. A reprodução e a inspeção não fazem chamadas pagas.

Arquivo: `recordings/private/jev-20260921-103901-2321f0/vaccine.ln.json.gz`. O mesmo diretório contém `summary.json` e o histórico incremental `audit.jsonl`.

A conferência reconstruiu todas as 89 rodadas a partir das decisões registradas e obteve estado final exatamente igual. Verificou cobertura de todas as células elegíveis, invariantes físicos, conservação de antígeno e soma dos tokens do histórico. Resultados em `live-verification.json`; a suíte tem 45 testes sintéticos aprovados.
