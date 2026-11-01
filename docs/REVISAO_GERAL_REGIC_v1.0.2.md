# Revisão geral dos 60 distritos ordinários

Versão v1.0.2 da proposta territorial MSMP. Sem aprovação ou homologação institucional. Os 63 distritos existentes e seus códigos são preservados: RS 22, SC 18 e PR 23. RS01, SC01 e PR01 têm composição, nomes e mapas exatamente preservados. Nenhum distrito tem menos de quatro municípios.

A solução selecionada revisa 125 vínculos municipais e 49 composições ordinárias; os demais 11 distritos ordinários foram reavaliados e mantidos. Todos os 63 distritos são conectados no grafo de adjacência municipal, por fronteiras lineares superiores a um metro na malha integral IBGE 2024. Ilhas internas aos municípios não são inventadas nem eliminadas.

Critério principal: vínculos imediatos e arranjos populacionais da REGIC 2018. Critérios complementares: contiguidade, limites estaduais, preservação de um polo de referência por distrito existente, cautelas cartográficas da BC250 versão 2025 e equilíbrio do maior tempo entre duas sedes municipais de cada distrito. Polo de referência analítico não é sede institucional.

Foram comparadas 16 alternativas com polos preservados e trocas de fronteira. A busca utiliza peso principal 70% REGIC, 22% deslocamento e 8% geografia, com sensibilidades de 65/27/8. Os pesos são escolhas técnicas desta proposta, não parâmetros prescritos pelo IBGE. As restrições impedem piora do maior tempo estadual e do coeficiente de variação em cada UF. Entre os cenários admissíveis, foi selecionado o de maior retenção ponderada dos vínculos REGIC. A solução é heurística; não há prova de ótimo global.

O índice ponderado de vínculos ajustáveis retidos passa de 88,17% para 92,48%. O maior tempo interno estimado passa de 269 para 257 min no RS, 183 para 178 min em SC e 218 para 189 min no PR. O coeficiente de variação cai nas três UFs. Isso não significa que toda viagem individual ficou mais curta: a média dos maiores tempos pode aumentar ao equilibrar distritos menores.

Tempos: base REGIC de rotas e distâncias, rede 2021, tabela publicada em 2023, com 16.159 registros rodoviários entre municípios do Sul. Caminhos mínimos no grafo destas ligações fornecem estimativas compostas quando falta o par direto. Não são tempos de trânsito atual nem roteamento entre todos os endereços. O recorte de ligações pode superestimar trajetos ausentes da tabela.

Geografia: drenagem nomeada com extensão agregada de ao menos 100 km no recorte Sul, serras/maciços lineares e pontes operacionais rodoviárias da BC250. A triagem usa proximidade de fronteiras e não presume que todo rio seja intransponível. A ausência de ponte mapeada não prova ausência real. A penalidade geográfica agregada cai de 720,25 para 682,00. Não substitui vistoria de acessos.

Quatro nomes provisórios foram ajustados, com IDs e polos preservados: PR15 Campo Mourão e entorno; SC11 Caçador e entorno; SC15 Vale do Itajaí–Blumenau; SC17 Costa Esmeralda–Itapema. Os nomes são metadados versionados, sem reescrever o cadastro histórico.

Fontes oficiais:
- https://geoftp.ibge.gov.br/organizacao_do_territorio/divisao_regional/regioes_de_influencia_das_cidades/Regioes_de_influencia_das_cidades_2018_Resultados_definitivos/base_tabular/REGIC2018_Municipios_Hierarquia_e_regiao.xlsx
- https://geoftp.ibge.gov.br/organizacao_do_territorio/divisao_regional/regioes_de_influencia_das_cidades/Regioes_de_influencia_das_cidades_2018_Resultados_definitivos/base_tabular/REGIC2018_Rotas_Brasil.xlsx
- https://biblioteca.ibge.gov.br/visualizacao/livros/liv101987.pdf
- https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/shapefiles/bc_250_shapefiles_2026_03_03.zip

Snapshot de atribuições SHA256: d7942b0571c2735ab3e3a68ab157fe57a1e4312028a945f166a965a5ec534fff
Nomes distritais SHA256: 02c78d951af16973e344e2115151e4a368e695cb126f8904ca82b26afa0d2065
