# Atlas Territorial do Sul — versão local 1.1

**Projeto de regionalização hipotética, não oficial.** Três Estados Constituintes (RS, SC, PR), 63 Províncias (incluindo três Metrópoles Autônomas) e 1.191 municípios.

## O que já funciona neste pacote

- Mapa navegável da **camada das 63 Províncias com limites vetoriais reais consolidados a partir do IBGE 2024**; zoom, deslocamento, filtros por Estado Constituinte e seleção.
- Busca pelos **1.191 municípios**, com código IBGE, associação provincial, população do Censo 2022, área IBGE 2024 e região imediata.
- Lista municipal por Província e painel com quantidade de municípios, população, área e densidade.
- Marcações versionadas por Província: não revisada, em revisão, validada ou divergência.
- Editor de transferência de municípios de uma Província a outra **do mesmo Estado Constituinte**, com prévia dos limites, verificações geográficas, confirmação explícita e registro de justificativa, **após a importação das geometrias municipais**.
- Snapshots imutáveis em `versions/`, SHA-256, restauração de versões, desfazer persistente, exportação CSV/JSON/GeoJSON e auditoria.
- Backend FastAPI e visualizador leve em HTML/CSS/JavaScript/Canvas, executáveis somente no computador local. A opção sem React foi adotada para eliminar dependências de build no Windows e permitir execução com um único arquivo .bat.

## Estado atual das malhas municipais

Este pacote contém os 63 polígonos provinciais e os **1.191 polígonos municipais oficiais do IBGE 2024**, importados e validados em 10 de outubro de 2026. O conjunto possui exatamente RS 497, SC 295 e PR 399 códigos municipais, sem geometrias vazias ou inválidas.

O ZIP oficial do RS também contém as áreas operacionais Lagoa Mirim (`4300001`) e Lagoa dos Patos (`4300002`). Elas permanecem preservadas integralmente no ZIP original e registradas no relatório de procedência, mas não integram a contagem municipal. O aplicativo não inventa polígonos.

## Inicialização no Windows

1. Extraia o ZIP para uma pasta, por exemplo `C:\Projetos\Atlas-Sul`.
2. Tenha instalado **Python 3.10 ou superior** com acesso ao `pip` e conexão à internet para a primeira instalação de dependências.
3. Dê duplo clique em **`INICIAR_ATLAS.bat`**. O script cria `.venv`, instala as dependências e inicia o serviço exclusivamente em `127.0.0.1:5173`.
4. Abra `http://127.0.0.1:5173` no navegador. A camada das Províncias, busca e consulta municipal estarão operacionais.
5. Para ativar os polígonos municipais e o editor, siga a etapa seguinte.

> A primeira inicialização depende de instalar bibliotecas Python. Após a instalação, o servidor e os arquivos do mapa funcionam sem serviço remoto, inclusive offline. A rede é necessária novamente caso você opte pelo download automático das malhas IBGE.

## Importar os 1.191 polígonos municipais oficiais

Com as dependências instaladas, **feche o servidor** e execute **`IMPORTAR_MALHAS_IBGE.bat`**. O importador tenta obter as malhas municipais IBGE 2024 de RS, SC e PR e verifica os códigos municipais antes de gravar as geometrias. Em caso de sucesso, reabra `INICIAR_ATLAS.bat` e marque a camada de Municípios.

Caso o download automático falhe, baixe estes três ZIPs oficiais em seu navegador:

- RS: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/RS/RS_Municipios_2024.zip
- SC: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/SC/SC_Municipios_2024.zip
- PR: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/PR/PR_Municipios_2024.zip

Então rode no PowerShell, dentro da pasta do Atlas:

```powershell
.\.venv\Scripts\python.exe scripts\importar_malhas_ibge.py --rs "C:\Downloads\RS_Municipios_2024.zip" --sc "C:\Downloads\SC_Municipios_2024.zip" --pr "C:\Downloads\PR_Municipios_2024.zip"
```

**Não importe malhas de anos distintos sem registrar explicitamente a diferença.** O importador exige 497, 295 e 399 polígonos municipais, exatamente os 1.191 códigos presentes no cadastro-base, e geometrias válidas. Ele gera `data/processed/municipios_map.geojson` (visão simplificada) e `data/processed/municipios_geometry_full.geojson` (geometrias integrais usadas na validação). Originais ZIP e seus hashes ficam em `data/original/` e no relatório de importação.

## Como transferir um município após importar a malha

1. Busque o município por nome ou código IBGE, ou marque a camada *Municípios* e clique em sua geometria.
2. Ative **Modo de edição territorial**.
3. Selecione a Província de destino do mesmo Estado Constituinte.
4. Clique em **Pré-visualizar transferência** e alterne **Antes / Depois**.
5. Confira população e área transferidas, adjacência por fronteira compartilhada e eventuais alterações nos componentes territoriais. Um alerta topológico exige revisão e não substitui inspeção humana.
6. Informe uma justificativa (opcional) e confirme. Origem e destino voltam a **Em revisão**.
7. Em **Histórico**, restaure qualquer versão anterior. **Desfazer** reverte a última modificação, registrando uma nova versão, sem apagar histórico.

Uma transferência não modifica a população, área ou quantidade total dos Estados Constituintes; apenas muda a Província responsável por aquele município. As geometrias são recalculadas a partir dos mesmos polígonos municipais originais.

## Organização

- `source-package/`: pacote de planejamento histórico RS/SC/PR, regras e scripts originais preservados.
- `data/original/`: cadastro Excel original, arquivos originais das Províncias e de auditoria; malhas ZIP oficiais quando forem importadas.
- `data/processed/municipios_baseline.json`: **fonte municipal de consulta inicial** com 1.191 códigos IBGE.
- `data/processed/provincias_map.geojson`: geometrias provinciais simplificadas apenas para exibição no mapa.
- `backend/server.py`: API local, validação cadastral e versionamento transacional por snapshot.
- `frontend/`: interface responsiva e visualizador Canvas, sem serviços de mapas externos obrigatórios.
- `scripts/importar_malhas_ibge.py`: integração das malhas oficiais municipais (etapa pendente).
- `scripts/auditar_baseline.py`: auditoria automática de composição e correspondência com regras históricas.
- `versions/`: snapshots imutáveis; `CURRENT.json` é o ponteiro atual de versão.
- `reports/`: divergências, verificações e mapa de referência em PNG.
- `docs/`: status, continuidade e histórico de mudanças.

## Verificações executadas nesta entrega

- 1.191 códigos municipais únicos: RS 497, SC 295, PR 399.
- 63 Províncias com identificação única: RS 22, SC 18, PR 23.
- População Censo 2022 total de RS 10.882.965, SC 7.610.361, PR 11.444.380 nos dados recuperados.
- Nenhuma divergência entre os 1.191 vínculos constantes no cadastro da Biblioteca e as regras territoriais contidas no pacote histórico.
- Testes de API concluídos: inspeção de cadastro, exportação, bloqueio de mudança entre Estados, bloqueio por falta de malha, status de validação, versões e reversões, transferência com geometrias **sintéticas isoladas em memória**.

Para reproduzir testes, execute no ambiente Python configurado:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\auditar_baseline.py
```

**Pendências antes de declarar o Atlas institucionalmente homologado:** revisar visualmente a composição de cada Província e registrar a homologação competente. A importação técnica das três malhas municipais está concluída. Não há integração eleitoral nesta etapa.

## Versão pública somente leitura

O mesmo código possui agora um modo próprio para publicação na internet. Ative-o com `ATLAS_PUBLIC_READ_ONLY=1`. Nesse modo, consultas, mapa, busca, histórico sanitizado e exportações permanecem disponíveis, enquanto prévias de transferência e todas as operações de escrita respondem `403` e os controles administrativos ficam ocultos.

Para testar no Windows, execute `INICIAR_ATLAS_PUBLICO.bat`; a edição pública abre em `http://127.0.0.1:5174` sem interferir no Atlas administrativo da porta 5173.

A configuração proposta para hospedagem está em `render.yaml`. Consulte `docs/HOSPEDAGEM_PUBLICA.md` antes de criar o repositório ou publicar o serviço. O modo público não substitui autenticação nem armazenamento persistente: ele é deliberadamente somente leitura.
