# Simulador de Rede de Filas

Este é um simulador para redes de filas que suporta topologias e configurações arbitrárias. O simulador é implementado em Python e utiliza arquivos de configuração YAML para definir a estrutura da rede.

## Requisitos

- Python 3.7 ou superior
- Pacote PyYAML

## Instalação

1. Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```

## Configuração

A configuração da rede é definida em um arquivo YAML (ex: `configuracao_rede.yml`). O arquivo de configuração especifica:

- Tipos de fila (formato G/G/s/c)
- Distribuições de tempo de chegada e serviço
- Probabilidades de roteamento entre filas

Exemplo de configuração:
```yaml
filas:
  fila1:
    tipo: "G/G/1"
    chegada:
      min: 2.0
      max: 4.0
    servico:
      min: 1.0
      max: 2.0
    roteamento:
      - fila2: 1.0
```

## Executando a Simulação

Para executar a simulação:

```bash
python simulador_rede_filas.py
```

O simulador irá:
1. Carregar a configuração da rede do arquivo `configuracao_rede.yml`
2. Executar a simulação para 100.000 eventos
3. Imprimir estatísticas para cada fila, incluindo:
   - Número de clientes perdidos
   - Distribuição de estados (porcentagem de tempo em cada estado)
   - Tempo total de simulação

## Formato da Saída

Os resultados da simulação mostrarão:
- Estatísticas de cada fila na rede
- Número de clientes perdidos em cada fila
- Distribuição de estados mostrando a porcentagem de tempo gasto em cada estado
- Tempo total de simulação

## Exemplo

A configuração fornecida simula uma rede de três filas onde:
1. Fila 1: G/G/1 com chegadas entre 2.0 e 4.0, serviço entre 1.0 e 2.0
2. Fila 2: G/G/2/5 com serviço entre 4.0 e 8.0
3. Fila 3: G/G/2/10 com serviço entre 5.0 e 15.0

Os clientes fluem da Fila 1 → Fila 2 → Fila 3.

