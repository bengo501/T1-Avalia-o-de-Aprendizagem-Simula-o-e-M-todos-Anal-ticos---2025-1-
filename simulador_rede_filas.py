import random
import yaml
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Cliente:
    """
    Classe que representa um cliente no sistema.
    id: identificador único do cliente
    tempo_chegada: momento em que o cliente chegou à fila atual
    fila_atual: nome da fila onde o cliente está
    proxima_fila: nome da próxima fila para onde o cliente será direcionado (se houver)
    """
    id: int
    tempo_chegada: float
    fila_atual: str
    proxima_fila: Optional[str] = None

class GeradorAleatorio:
    """
    Implementação do gerador linear congruente para geração de números pseudo-aleatórios.
    Este gerador é usado para simular tempos de chegada e serviço.
    """
    def __init__(self, seed=1, a=1664525, c=1013904223, M=2**32):
        self.anterior = seed
        self.a = a
        self.c = c
        self.M = M
    
    def ProximoAleatorio(self):
        """
        Gera o próximo número pseudo-aleatório usando o método linear congruente.
        Retorna um número entre 0 e 1.
        """
        self.anterior = (self.a * self.anterior + self.c) % self.M
        return self.anterior / self.M if self.M != 0 else 0

class Fila:
    """
    Classe que representa uma fila no sistema.
    Gerencia o estado da fila, incluindo servidores, clientes em espera e estatísticas.
    """
    def __init__(self, nome: str, config: dict):
        self.nome = nome
        self.tipo = config['type']
        # Extrai o número de servidores do tipo da fila (ex: G/G/2/5 -> 2 servidores)
        partes_tipo = self.tipo.split('/')
        self.num_servidores = int(partes_tipo[2]) if len(partes_tipo) > 2 else 1
        # Extrai a capacidade da fila (ex: G/G/2/5 -> capacidade 5)
        self.capacidade = int(partes_tipo[3]) if len(partes_tipo) > 3 else float('inf')
        
        # Configuração dos tempos de chegada e serviço
        self.tempo_chegada_min = config.get('arrival', {}).get('min', 0)
        self.tempo_chegada_max = config.get('arrival', {}).get('max', 0)
        self.tempo_servico_min = config['service']['min']
        self.tempo_servico_max = config['service']['max']
        
        # Configuração do roteamento (para qual fila os clientes irão após o serviço)
        self.roteamento = config.get('routing', [])
        
        # Estado da fila
        self.fila: List[Cliente] = []  # Lista de clientes em espera
        self.servidores: List[Tuple[Optional[Cliente], float]] = [(None, 0)] * self.num_servidores
        self.clientes_perdidos = 0
        self.tempo_em_estado = defaultdict(float)  # Tempo acumulado em cada estado
        self.ultimo_tempo_evento = 0
        self.gerador = GeradorAleatorio()

    def gerar_tempo_servico(self) -> float:
        """
        Gera um tempo de serviço aleatório entre o mínimo e máximo configurados.
        """
        return self.tempo_servico_min + (self.tempo_servico_max - self.tempo_servico_min) * self.gerador.ProximoAleatorio()

    def gerar_tempo_chegada(self, tempo_atual: float) -> float:
        """
        Gera o próximo tempo de chegada.
        Se a fila não tem chegadas próprias (min=max=0), retorna infinito.
        """
        if self.tempo_chegada_min == 0 and self.tempo_chegada_max == 0:
            return float('inf')
        return tempo_atual + self.tempo_chegada_min + (self.tempo_chegada_max - self.tempo_chegada_min) * self.gerador.ProximoAleatorio()

    def obter_proxima_fila(self) -> Optional[str]:
        """
        Determina para qual fila o cliente será direcionado após o serviço.
        Por enquanto, sempre retorna a primeira opção de roteamento.
        """
        if not self.roteamento:
            return None
        return list(self.roteamento[0].keys())[0]

class SimuladorRede:
    """
    Classe principal que gerencia a simulação da rede de filas.
    Coordena o fluxo de clientes entre as filas e coleta estatísticas.
    """
    def __init__(self, arquivo_config: str, num_eventos: int = 100000):
        # Carrega a configuração da rede do arquivo YAML
        with open(arquivo_config, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.num_eventos = num_eventos
        self.relogio = 0  # Tempo atual da simulação
        self.eventos = []  # Lista de eventos futuros
        self.filas: Dict[str, Fila] = {}
        self.contador_clientes = 0
        
        # Inicializa todas as filas da rede
        for nome_fila, config_fila in self.config['queues'].items():
            self.filas[nome_fila] = Fila(nome_fila, config_fila)
        
        # Agenda as chegadas iniciais para filas que têm taxa de chegada
        for nome_fila, fila in self.filas.items():
            if fila.tempo_chegada_min > 0 or fila.tempo_chegada_max > 0:
                self.agendar_evento("chegada", fila.gerar_tempo_chegada(2.0), nome_fila)

    def agendar_evento(self, tipo_evento: str, tempo: float, nome_fila: str, cliente: Optional[Cliente] = None):
        """
        Agenda um novo evento para ser processado no futuro.
        Os eventos são ordenados por tempo para garantir o processamento na ordem correta.
        """
        self.eventos.append((tempo, tipo_evento, nome_fila, cliente))
        self.eventos.sort()

    def processar_chegada(self, nome_fila: str, cliente: Optional[Cliente] = None):
        """
        Processa a chegada de um cliente em uma fila.
        Se o cliente não for fornecido, cria um novo cliente.
        Se a fila estiver cheia, incrementa o contador de clientes perdidos.
        """
        fila = self.filas[nome_fila]
        
        if cliente is None:
            self.contador_clientes += 1
            cliente = Cliente(
                id=self.contador_clientes,
                tempo_chegada=self.relogio,
                fila_atual=nome_fila,
                proxima_fila=fila.obter_proxima_fila()
            )
        else:
            # Atualiza a fila atual do cliente
            cliente.fila_atual = nome_fila
            # Determina a próxima fila para onde o cliente será direcionado
            cliente.proxima_fila = fila.obter_proxima_fila()

        # Verifica se a fila está cheia
        if len(fila.fila) >= fila.capacidade:
            fila.clientes_perdidos += 1
            return

        # Adiciona o cliente à fila
        fila.fila.append(cliente)
        
        # Agenda a próxima chegada se esta fila tem taxa de chegada
        if fila.tempo_chegada_min > 0 or fila.tempo_chegada_max > 0:
            self.agendar_evento("chegada", fila.gerar_tempo_chegada(self.relogio), nome_fila)

        # Tenta iniciar o serviço para o cliente recém-chegado
        for i in range(fila.num_servidores):
            if fila.servidores[i][0] is None and fila.fila:
                self.iniciar_servico(nome_fila, i)

    def iniciar_servico(self, nome_fila: str, indice_servidor: int):
        """
        Inicia o serviço para um cliente em um servidor específico.
        Agenda o evento de partida para o momento em que o serviço será concluído.
        """
        fila = self.filas[nome_fila]
        if fila.fila:
            cliente = fila.fila.pop(0)
            tempo_servico = fila.gerar_tempo_servico()
            fila.servidores[indice_servidor] = (cliente, self.relogio + tempo_servico)
            self.agendar_evento("partida", self.relogio + tempo_servico, nome_fila, cliente)

    def processar_partida(self, nome_fila: str, cliente: Cliente):
        """
        Processa a partida de um cliente após o serviço.
        Libera o servidor e direciona o cliente para a próxima fila ou para fora do sistema.
        """
        fila = self.filas[nome_fila]
        
        # Encontra e libera o servidor
        for i in range(fila.num_servidores):
            if fila.servidores[i][0] and fila.servidores[i][0].id == cliente.id:
                fila.servidores[i] = (None, 0)
                break

        # Direciona para a próxima fila ou para fora do sistema
        if cliente.proxima_fila:
            # Cria uma cópia do cliente para enviar para a próxima fila
            novo_cliente = Cliente(
                id=cliente.id,
                tempo_chegada=self.relogio,
                fila_atual=cliente.proxima_fila,
                proxima_fila=None  # Será definido quando chegar à próxima fila
            )
            self.processar_chegada(cliente.proxima_fila, novo_cliente)
        else:
            pass  # Cliente sai do sistema

        # Tenta iniciar serviço para o próximo cliente
        for i in range(fila.num_servidores):
            if fila.servidores[i][0] is None and fila.fila:
                self.iniciar_servico(nome_fila, i)

    def executar(self):
        """
        Executa a simulação até atingir o número de eventos especificado.
        Processa eventos na ordem cronológica e coleta estatísticas.
        """
        print(f"Iniciando simulação da rede com {self.num_eventos} eventos...")
        
        eventos_processados = 0
        while eventos_processados < self.num_eventos and self.eventos:
            self.relogio, tipo_evento, nome_fila, cliente = self.eventos.pop(0)
            
            # Atualiza o tempo em estado para todas as filas
            for fila in self.filas.values():
                tempo_decorrido = self.relogio - fila.ultimo_tempo_evento
                # Conta clientes em serviço + clientes na fila
                num_clientes_na_fila = len(fila.fila)
                num_clientes_em_servico = sum(1 for s in fila.servidores if s[0] is not None)
                estado_atual = num_clientes_na_fila + num_clientes_em_servico
                fila.tempo_em_estado[estado_atual] += tempo_decorrido
                fila.ultimo_tempo_evento = self.relogio

            if tipo_evento == "chegada":
                self.processar_chegada(nome_fila, cliente)
            elif tipo_evento == "partida":
                self.processar_partida(nome_fila, cliente)

            eventos_processados += 1
            if eventos_processados % 10000 == 0:
                print(f"Processados {eventos_processados} eventos. Tempo atual: {self.relogio:.2f}")

        # Imprime os resultados
        print("\nResultados da Simulação:")
        print("=" * 50)
        for nome_fila, fila in self.filas.items():
            print(f"\nFila: {nome_fila} ({fila.tipo})")
            print(f"Clientes perdidos: {fila.clientes_perdidos}")
            print("Distribuição de estados:")
            tempo_total = sum(fila.tempo_em_estado.values())
            for estado, tempo in sorted(fila.tempo_em_estado.items()):
                porcentagem = (tempo / tempo_total * 100) if tempo_total > 0 else 0
                print(f"Estado {estado}: {porcentagem:.2f}%")
        
        print(f"\nTempo total de simulação: {self.relogio:.2f}")

if __name__ == "__main__":
    simulador = SimuladorRede("configuracao_rede.yml")
    simulador.executar() 