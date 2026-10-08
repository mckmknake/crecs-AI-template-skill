# Uso — exemplos práticos

Todos os exemplos usam `S=scripts/crecs_template.py` e uma área de trabalho em
`./work`. Qualquer comando aceita `--json` para saída legível por máquina e `--help`
para ver suas opções.

## 0. Preparar

```bash
S=scripts/crecs_template.py

# Copie o perfil e preencha com os dados do cliente.
cp assets/target-profile.example.json ./acme-profile.json
# edite: site_host, preview_slug, popups

python3 $S init \
    --from assets/property-template-all-widgets.json \
    --workdir ./work \
    --profile ./acme-profile.json
```

Para partir do export atual do cliente em vez do template-base:

```bash
python3 $S init --from ./export-atual.json --workdir ./work --profile ./acme-profile.json
```

Antes de confiar em qualquer resposta, confirme que o pacote está íntegro:

```bash
python3 $S selftest
```

## 1. Mudar somente uma cor

> "Deixe o card de campos branco."

```bash
python3 $S inspect --workdir ./work --widgets
# ...  b133d6f  crecs_property_fields  #3:section/...

python3 $S set --workdir ./work --element b133d6f \
    --key card_color --value "#FFFFFF" \
    --decision "A Acme pediu cards de campo brancos."

python3 $S diff --workdir ./work
```

O diff mostra uma linha. Nada mais se move.

## 2. Reorganizar blocos

> "Coloque o card de detalhes acima da caixa de mídia."

```bash
python3 $S move --workdir ./work --element 39f1774c --before 61b0cce6
```

Os IDs de elemento sobrevivem ao movimento, então bindings e estilos acompanham. O
comando recusa qualquer movimento que coloque um widget antes do loader.

## 3. Só no mobile

> "Menos padding no celular, sem mexer no desktop."

```bash
python3 $S set --workdir ./work --element b133d6f \
    --key card_padding --device mobile \
    --value '{"unit":"px","top":"6","right":"6","bottom":"6","left":"6","isLinked":true}'
```

Só `card_padding_mobile` é escrito. O mesmo com `card_color` é recusado — aquele
controle não é responsivo, então o Elementor nunca leria a variante:

```
'card_color' on crecs_property_fields is not a responsive control (is_responsive is
false), so Elementor never reads a mobile variant of it.
```

## 4. Tipografia e hover

> "Links de anexo das suites mais fortes, outra cor no hover, menor no tablet."

```bash
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_typography_typography --value custom
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_typography_font_weight --value 700
python3 $S set --workdir ./work --element 39f1774c --key attachment_link_text_color_hover --value "#3B82F6"
python3 $S set --workdir ./work --element 39f1774c \
    --key attachment_link_typography_font_size --device tablet \
    --value '{"unit":"px","size":13,"sizes":[]}'
```

`--value 700` é gravado como a string `"700"`, porque é isso que a lista de opções do
controle guarda — o comando avisa quando faz essa conversão.

Atenção: `attachment_link_*` existe em `crecs_property_suites` e **não** existe em
`crecs_property_attachments`, onde o link é estilizado por `card_body_*`. A ferramenta
recusa e diz qual é o controle certo.

## 5. Adicionar um widget

```bash
python3 $S inspect --workdir ./work --tree --json | head -40   # ache o id da coluna
python3 $S add-widget --workdir ./work --widget crecs_property_rates --into 6f64db7d \
    --settings '{"property_rate":"both","rate_style":"inline-block"}'
```

Um segundo `crecs_property_map` é recusado, com o motivo técnico:

```
crecs_property_map already appears 1 time(s) and at most 1 can work on one page.
Declares the global JS function crecs_map_widget_plot_pov without an instance suffix
and a textarea with the fixed id property_geodata.
```

## 6. Remover um bloco

```bash
python3 $S remove --workdir ./work --element 552329d1 \
    --reason "A Acme nunca preenche demográficos."
```

`--reason` é obrigatório e vai para `decisions.md`. Remover o loader exige `--force` e
o comando explica primeiro o que quebra. Um imóvel sem dados para um bloco não é
motivo para retirar o bloco do template que todos os imóveis compartilham — o widget
simplesmente não renderiza nada quando está vazio.

## 7. Ligar um campo do imóvel

```bash
python3 $S catalog --params | grep -i size
python3 $S bind --workdir ./work --element 31338650 --control title --param property_name
python3 $S unbind --workdir ./work --element 31338650 --control title
```

A grafia errada é detectada:

```
'size-available_sf' is not a param_name that
Crecs_Functions::crecs_parse_property_data() produces. The real key is
'size-available_SF' — keys are compared exactly, including case.
```

## 7b. Reapontar os popups de contato

O template entregue liga seus dois botões de contato aos popups do Elementor Pro do
site de referência, 4554 e 4646. Esses ids não significam nada em outro site, então o
`validate` recusa o export até que sejam reapontados. O perfil de exemplo traz ids de
popup como placeholder pelo mesmo motivo: um id numérico ali pareceria a afirmação de
que aquele popup existe.

```bash
python3 $S popup --workdir ./work --list
```

```
ELEMENT    TYPE                     CONTROL    POPUP    DECLARED
2121e6fe   button                   link       4554     NO
55f63989   button                   link       4646     NO
```

Coloque os ids reais do cliente no mapa `popups` do perfil e então:

```bash
python3 $S popup --workdir ./work --element 2121e6fe --control link \
    --set 4581 --decision "Popup de consultor da Acme."
```

Um id que o perfil não declara é recusado, e um id não numérico também. Se o cliente
não tem popup equivalente, `--clear` remove o binding; deixá-lo apontando para o id de
um estranho é a única opção que não existe.

## 8. Validar

```bash
python3 $S validate --workdir ./work
python3 $S validate --workdir ./work --level error     # só o que bloqueia o export
python3 $S validate --workdir ./work --json | python3 -m json.tool | head -40
```

Código de saída `0` sem erros e `2` quando há erros.

As três severidades:

- **ERROR** bloqueia um export "pronto": chave inventada, valor fora de um vocabulário
  fechado, variante de dispositivo em controle não responsivo, binding corrompido,
  `param_name` inexistente, ID duplicado, aninhamento inválido, mais instâncias do que
  o widget suporta, dependência do site não resolvida, algo com forma de credencial, ou
  o imóvel de exemplo congelado.
- **WARNING** não bloqueia: chave de uma versão antiga do plugin (o relatório diz qual
  controle a substituiu), chave desconhecida que já estava no documento, asset de outro
  site, widget pertinente ausente, valor de opção que o Elementor renomeou.
- **INFO** é contexto: cores literais em vez de tokens globais, famílias de fonte,
  controle cuja condição não está satisfeita, chave interna do Elementor.

Uma chave desconhecida **preexistente** é preservada e sinalizada. Uma **nova** sem
contrato confirmado é bloqueada. Nada é apagado por ser desconhecido.

## 9. Desfazer, histórico, retomar

```bash
python3 $S history --workdir ./work
python3 $S undo --workdir ./work
python3 $S undo --workdir ./work --steps 3
```

`history` imprime tudo que outra sessão precisa: revisão, hash do documento, perfil,
versão do catálogo e cada decisão registrada. O undo também é uma revisão, então pode
ser desfeito.

Se alguém editar `work/document.json` por fora, o próximo comando recusa em vez de
sobrescrever:

```
document.json changed outside this tool since revision 4, so committing would discard
that edit. Re-run with --accept-external to take the file as it is now.
```

## 10. Exportar

```bash
python3 $S export --workdir ./work --out ./acme-property-page.json
```

Saem dois arquivos: o JSON do Elementor e `acme-property-page.json.report.json` com as
contagens, os mapeamentos de perfil aplicados e o nível da afirmação. Um export
bloqueado não escreve nada e lista cada achado que bloqueou. `--allow-draft` salva um
rascunho incompleto, identificado como tal.

Depois o modelo entra no WordPress, e essa parte o assistente faz no navegador
(SKILL.md, *Deliver it*): salva o arquivo na pasta Downloads da pessoa, abre
**Modelos → Modelos Salvos → Importar Modelos**, a pessoa escolhe o arquivo e clica em
**Importar agora** e, com o "sim" dela, o assistente coloca o número do modelo novo em
**CRE Cloud Solutions → Custom Property Page Template** (a opção
`crecs_custom_property_page_template_shortcode`). Um modelo só serve todos os imóveis,
então isso é feito uma vez, não por imóvel.

### Sem pasta de projeto

Nada acima exige uma pasta sua. Omita `--workdir` e o workspace vai para um diretório
fixo dentro do temp do sistema, que todo comando imprime; `$CRECS_WORKDIR` muda o lugar.
Peça `--out -` e o JSON do Elementor sai em stdout em vez de virar arquivo:

```bash
python3 $S init --from assets/property-template-all-widgets.json --profile ./acme.json
python3 $S set --element 39f1774c --key card_header_color --value "#FFFFFF"
python3 $S export --out - > acme-property-page.json
```

O stdout leva o JSON e mais nada — o resumo e qualquer recusa vão para stderr — então
ele redireciona limpo ou vai anexado numa resposta. Nesse modo nenhum `.report.json` é
escrito, porque não há caminho onde colocá-lo ao lado; rode `validate` para ver os
achados.

**Nada neste pacote foi importado nem renderizado.** Um export aprovado significa que o
JSON é estruturalmente válido e coerente com os controles do plugin instalado. Se está
bonito, só o navegador responde.

## 11. Explorar o catálogo

```bash
python3 $S catalog --list-widgets
python3 $S catalog --widget crecs_property_suites --controls
python3 $S catalog --widget crecs_property_suites --controls --section card_body_section
python3 $S catalog --params
python3 $S coverage
```

Ou leia `references/widgets/<widget>.md`, que é a mesma informação escrita para
pessoas.

## 12. Rodar os testes

```bash
python3 scripts/tests/run_tests.py              # tudo, com relatório de cobertura
python3 scripts/tests/run_tests.py --unit       # rápido
python3 scripts/tests/run_tests.py --conversational
python3 scripts/tests/run_tests.py --json
```

Offline, só biblioteca padrão.

## 13. Página de busca

A página que lista os imóveis — mapa, filtros, cards; normalmente `/properties` — não é
um template do Elementor: tem ferramenta própria, `scripts/crecs_search.py`, e passa
pela mesma prévia. No WordPress, **CRE Cloud Solutions → Template preview → Start search
page preview** mostra o arquivo de sessão numa caixa (com `"kind": "search"`). O
assistente lê essa caixa na própria página e salva sozinho; a pessoa não copia nada:

```bash
python3 scripts/crecs_preview.py connect <<'EOF'
(o texto da caixa, como a página mostra)
EOF
# connected to example.com: the search page preview. Session saved in ~/.crecs/preview-example.com.json
```

Se depois a prévia disser que a sessão expirou ou que o token mudou, **New link** nessa
sessão, na mesma tela, mostra uma caixa nova: é só fazer o `connect` dela do mesmo jeito.

> "Quero os filtros numa coluna à esquerda, com botões azuis, e o mapa mais baixo no
> celular."

```bash
P=scripts/crecs_preview.py
B=scripts/crecs_search.py
F=./busca.json
SESSION=~/.crecs/preview-example.com.json    # o arquivo de sessão que o connect salvou

python3 $P current --out $F --session-file $SESSION    # o que a prévia mostra agora
python3 $B show --file $F                                    # a árvore, com os ids

# filtros e resultados lado a lado, numa caixa; empilhados no tablet e no celular
python3 $B add-box --file $F --wrap 5e2a0005,5e2a000d --direction row --id lado0001
python3 $B set --file $F --node lado0001 --key direction --device tablet --value column
python3 $B set --file $F --node 5e2a0002 --key direction --value column    # a área principal segue o layout
python3 $B set --file $F --node 5e2a0005 --key _width --value 300px
python3 $B set --file $F --node 5e2a000d --key _grow --value yes

# o botão de tipo de imóvel azul, com hover, e o texto em português
python3 $B set --file $F --node 5e2a0008 --key button_background_color --value "#0a3d62"
python3 $B set --file $F --node 5e2a0008 --key button_background_color --hover --value "#145a8d"
python3 $B text --file $F --node 5e2a0008 --slot button --value "Tipo de imóvel"

# o mapa mais baixo só no celular
python3 $B set --file $F --node 5e2a0004 --key map_height --device mobile --value 240px

python3 $B validate --file $F
python3 $P apply --document $F --session-file $SESSION    # a prévia recarrega
```

Com o que a página começa, e quais filtros aparecem:

> "Abra a página já em imóveis para locação, ofereça só Office, Retail e Industrial na
> lista de tipos e esconda o filtro de preço no celular."

```bash
python3 $P options --session-file $SESSION    # os nomes de tipos e corretores do próprio site
python3 $B set --file $F --node 5e2a0007 --key start_for_lease --value yes
python3 $B set --file $F --node 5e2a0008 --key offer --value "Office, Retail, Industrial"
python3 $B hide --file $F --node 5e2a000a --device mobile
python3 $P apply --document $F --session-file $SESSION
```

Um valor inicial é um padrão, não uma trava: o visitante vê For Lease marcado e pode
desmarcar, ou apertar Limpar, que limpa todos os filtros. Enquanto nada estiver
marcado, uma lista reduzida busca só os nomes que oferece. Use os nomes do `options`;
um nome com vírgula vai em JSON: `--value '["Bryan King, CCIM"]'`.

Os ids vêm do `show`. `controls --node <id>` lista cada configuração de um bloco e o
que ela aceita; `references/search/SEARCH-LAYOUT.md` explica todos os blocos. Uma
mudança que o plugin recusaria não é gravada, e o comando diz o motivo — a ordenação,
por exemplo, não pode entrar nos filtros, porque o botão Limpar a zeraria.

Nada disso muda o site. Quem publica é a pessoa, no botão **Publish** da prévia e depois
em **Yes, publish** na faixa que aparece (só administradores); uma faixa verde confirma.
Funciona também no navegador do app do Claude: não há janela do navegador nem botão OK.
Só um plugin anterior à 2.8.10 pergunta com a janela do próprio navegador, que o
navegador do app do Claude nunca mostra; num site assim, publique por outro navegador.
`crecs_preview.py published` diz ao assistente se o layout na tela está no ar, para ele
conferir em vez de supor. A tela Template preview mostra o layout no ar e devolve
qualquer um dos anteriores, ou o original.

## Regras que realmente quebram a página

- `crecs_property_data` precisa ser o **primeiro** widget: ele resolve o imóvel e
  escreve em `$_SESSION['property']`, que todos os outros widgets leem no próprio
  `render()`.
- O `slug` do loader **não é resto de dado**: é o fallback de tempo de design, usado no
  editor do Elementor e em qualquer URL que não seja `/property/{slug}`. Vazio, a
  prévia do editor não resolve imóvel nenhum.
- Quatro widgets só podem aparecer uma vez (`crecs_property_data`,
  `crecs_property_map`, `crecs_property_docs`, `crecs_property_team_members`, mais
  `crecs_property_meta_tags`). O resto escopa os IDs de DOM pelo ID do elemento, por
  isso as **duas** instâncias de `crecs_property_suites` do template-base são legítimas.
- Seções e colunas, não containers. O site auditado usa o modelo clássico.
