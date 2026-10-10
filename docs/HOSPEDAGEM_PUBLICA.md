# Versão pública do Atlas Territorial do Sul

## Objetivo

A versão pública permite consultar o mapa, as 63 Províncias e os 1.191 municípios sem conceder ao visitante qualquer capacidade de alterar vínculos territoriais, estados de revisão ou histórico.

Ela é ativada pela variável de ambiente:

```text
ATLAS_PUBLIC_READ_ONLY=1
```

Sem essa variável, a execução local administrativa continua funcionando como antes.

## Proteções aplicadas

- A interface identifica a edição como **Consulta pública**.
- Controles de edição, validação, transferência, restauração e desfazer ficam ocultos.
- A API responde `403` a prévias de transferência e a todas as rotas de escrita.
- Swagger, ReDoc e o documento OpenAPI ficam desativados no modo público.
- O histórico público remove justificativas e avisos internos, mantendo somente os campos territoriais necessários à auditoria pública.
- O modo público usa o mapa provincial consolidado e o GeoJSON municipal simplificado. A geometria municipal integral permanece fora do pacote público.

## Interação em dispositivos móveis

- O mapa trata o toque curto como seleção e só inicia o deslocamento depois de um movimento deliberado do dedo.
- O teste de seleção considera a densidade real de pixels da tela, inclusive em celulares de alta resolução.
- Toques em limites estreitos recebem uma pequena tolerância espacial; as geometrias oficiais não são alteradas.
- Cancelamentos de gesto e perda de captura do ponteiro encerram a interação sem deixar o mapa preso em estado de arraste.

## Arquivos que devem ir ao repositório de hospedagem

- `backend/`
- `frontend/`
- `data/processed/municipios_baseline.json`
- `data/processed/provincias_map.geojson`
- `data/processed/municipios_map.geojson`
- `versions/CURRENT.json`
- `versions/v1.0.0.json`
- `requirements.txt`
- `render.yaml`

O `.gitignore` impede a inclusão do ambiente virtual, dos ZIPs originais, dos pacotes históricos, dos relatórios de trabalho e da geometria municipal integral.

## Publicação proposta na Render

O arquivo `render.yaml` prepara um Web Service gratuito com:

- instalação por `pip install -r requirements.txt`;
- inicialização por Uvicorn em `0.0.0.0:$PORT`;
- verificação de saúde em `/api/status`;
- modo público somente leitura ativado;
- publicação automática desativada para exigir decisão explícita antes de cada nova implantação.

O endereço final será um subdomínio da própria Render, semelhante a:

```text
https://atlas-territorial-sul.onrender.com
```

O nome exato depende da disponibilidade no momento da criação do serviço.

## Limite deliberado

Esta edição não é uma plataforma colaborativa. Para permitir edição pública ou administrativa pela internet serão necessários autenticação, autorização por função, armazenamento persistente e trilha de auditoria em banco de dados.
