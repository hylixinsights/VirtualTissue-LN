# Demonstração gravada: divisão e memória com Jev

[▶ Abrir a demonstração 3D](http://127.0.0.1:8010/?recording=231bd6719cad444a8d0d)

Use **Play recording** para acompanhar a trajetória inteira ou os atalhos **GC formed**, **Memory B** e **First division** para mostrar os eventos principais. A reprodução não faz chamadas à API.

## O que foi observado

O exemplo começa com 100 células individuais em um disco de uma camada e termina em **64 horas simuladas**, após **12.284 decisões reais do Jev**. Modelo retornado: `jev-1.13.0`.

| Evento | Tempo simulado | Evidência |
|---|---:|---|
| Formação do GC | 22,5 h | Evento do núcleo biológico |
| Três células B de memória | 63 h | LN-0029, LN-0054, LN-0062 completaram o programa MEMORY |
| Uma divisão física | 64 h | LN-0058 foi substituída por LN-0101 e LN-0102, preservando o clone |

As células de memória pertencem a outros clones e surgiram antes dessa divisão. **Não são apresentadas como descendentes das duas filhas gravadas.** Não houve plasmócitos ou anticorpos neste exemplo.

Estado final: **99 células vivas = 100 iniciais + 1 ganho líquido da divisão − 2 mortes**; 13 B de GC, 7 Tfh e 3 B de memória. Uma divisão corresponde a um pai substituído por duas filhas, portanto acrescenta uma célula ao total. Os 160 pacotes de antígeno permanecem contabilizados, inclusive os degradados.

## Como o exemplo foi obtido

A gravação original de 44,5 horas foi preservada. Sua continuação até 60 horas, com o mesmo contexto decisório, não produziu divisão nem memória. Uma primeira revisão explicou ao Jev os estados celulares e as licenças finitas; essa comparação chegou a quatro divisões, mas não a memória ou plasma, e foi preservada até 86,5 horas.

A demonstração final parte do mesmo checkpoint de **60 horas**. A partir desse ponto, o contexto v4 explicita uma **hipótese qualitativa de demonstração**: a escassez local de antígeno cognato pode favorecer preservação como memória em vez de iniciar outro ciclo de seleção dependente de antígeno. Antígeno disponível e ajuda renovada permitem considerar reciclagem ou secreção. Esse critério altera a política enviada ao Jev; não é uma taxa medida nem um resultado espontâneo sob o contexto anterior.

Todas as escolhas aplicadas foram retornadas pelo Jev, incluindo MEMORY e DIVIDE. Não houve substituição por decisões sintéticas, sorteio de destinos pelo código, criação manual de células de memória ou ajuste das probabilidades para impor uma escolha. Permaneceram as mesmas condições de elegibilidade, geometria, relógios, orçamento de divisão e inventário de antígeno. Não foi aplicado reforço de antígeno.

A execução terminou ao satisfazer o critério declarado de **divisão física e memória ou plasma maduro**. Portanto, este é um exemplo selecionado para demonstração, com revisão de contexto registrada, e não uma estimativa sem viés de frequência de destinos celulares. Os parâmetros continuam propostos e não calibrados para um linfonodo humano.

## Consumo de todas as tentativas

- 911 tentativas HTTP cumulativas, incluindo o exemplo original e a comparação sem memória.
- 25.859.657 tokens de entrada e 596.008 de saída informados pelo serviço.
- **US$ 1,086105594 de custo conhecido estimado**, aproximadamente **US$ 1,09**. O acréscimo em relação aos US$ 0,597968994 anteriores foi de aproximadamente **US$ 0,49**.
- Uma tentativa HTTP 400 anterior não informou consumo. Reservando o contexto máximo conservador de 65.536 tokens para ela, a margem adicional é US$ 0,002752512.
- O teto global de 1.800 tentativas foi conservadoramente limitado a US$ 4,9545216 pelo mesmo cálculo, abaixo da autorização de US$ 5. Não houve nova compra nem mudança de recarga.

O cálculo usa US$ 0,042 por milhão de tokens de entrada, saída gratuita e contexto máximo de 64k, conferidos na [documentação oficial do Jev](https://docs.typesafe.ai/models) em 21/09/2026. Não foi consultado o saldo final da conta.

## Verificação e arquivos

A auditoria reproduziu exatamente todas as 128 rodadas, confirmou que o trecho anterior a 60 horas é idêntico ao checkpoint e verificou cobertura das decisões individuais, ancestralidade das duas filhas, conservação de antígeno e soma dos tokens. Os 47 testes sintéticos passaram. A reprodução no navegador verifica os atalhos, os contadores, a divulgação da hipótese e ausência de novas chamadas de inferência.

- Demonstração: `recordings/private/jev-fate-demo-20260921/vaccine.ln.json.gz`.
- Comparação preservada: `recordings/private/jev-extended-demo-20260921/`.
- Original preservado: `recordings/private/jev-20260921-103901-2321f0/`.
- Auditoria final: `docs/demo-verification.json`.
- Contexto proposto: `docs/jev-fate-context.json`; descrições completas e versão no código `jev.py`.

O histórico de requisições da demonstração inclui os custos da comparação, identificados como tentativas não aplicadas a esta trajetória. O resumo e o arquivo de decisões distinguem essa proveniência; os valores cumulativos não devem ser somados novamente entre pastas, pois compartilham o mesmo trecho inicial.
