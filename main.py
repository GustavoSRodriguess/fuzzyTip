import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json
from tabulate import tabulate
import time

# antes de executar por favor instale todas as dependencias
# pip install numpy
# pip install skfuzzy
# pip install matplotlib
# pip install tabulate
# tem algumas outras que o skfuzzy usa, mas dai é só ver no log de erro pq n lembro

class CalculadoraGorjeta:
    def __init__(self):
        # criacao variais sistema fuzzy
        self.qualidade_refeicao = ctrl.Antecedent(np.arange(0, 11, 1), 'qualidade_refeicao')
        self.qualidade_servico = ctrl.Antecedent(np.arange(0, 11, 1), 'qualidade_servico')
        self.tempo_atendimento = ctrl.Antecedent(np.arange(0, 61, 1), 'tempo_atendimento')
        self.gorjeta = ctrl.Consequent(np.arange(0, 31, 1), 'gorjeta')
        
        # config conjuntos fuzzy
        self.configurar_conjuntos_fuzzy()
        
        # regras
        self.configurar_regras()
        
        # historico calculo
        self.historico = []
        self.carregar_historico()

    def configurar_conjuntos_fuzzy(self):
        # qualidade da refeicao 
        self.qualidade_refeicao['insossa'] = fuzz.trimf(self.qualidade_refeicao.universe, [0, 0, 5])
        self.qualidade_refeicao['normal'] = fuzz.trimf(self.qualidade_refeicao.universe, [0, 5, 10])
        self.qualidade_refeicao['saborosa'] = fuzz.trimf(self.qualidade_refeicao.universe, [5, 10, 10])

        # qualidade do servico
        self.qualidade_servico['ruim'] = fuzz.trimf(self.qualidade_servico.universe, [0, 0, 5])
        self.qualidade_servico['aceitavel'] = fuzz.trimf(self.qualidade_servico.universe, [0, 5, 10])
        self.qualidade_servico['excelente'] = fuzz.trimf(self.qualidade_servico.universe, [5, 10, 10])

        # tempo ateniemento
        self.tempo_atendimento['rapido'] = fuzz.trimf(self.tempo_atendimento.universe, [0, 0, 20])
        self.tempo_atendimento['mediano'] = fuzz.trimf(self.tempo_atendimento.universe, [10, 25, 40])
        self.tempo_atendimento['demorado'] = fuzz.trimf(self.tempo_atendimento.universe, [30, 60, 60])

        # tip
        self.gorjeta['sem_gorjeta'] = fuzz.trimf(self.gorjeta.universe, [0, 0, 5])
        self.gorjeta['pouca'] = fuzz.trimf(self.gorjeta.universe, [0, 10, 15])
        self.gorjeta['media'] = fuzz.trimf(self.gorjeta.universe, [10, 15, 20])
        self.gorjeta['generosa'] = fuzz.trimf(self.gorjeta.universe, [15, 30, 30])

    def configurar_regras(self):
        self.regras = [
            ctrl.Rule(self.qualidade_refeicao['insossa'] & self.qualidade_servico['ruim'], 
                     self.gorjeta['pouca']),
            ctrl.Rule(self.qualidade_refeicao['saborosa'] & self.qualidade_servico['excelente'], 
                     self.gorjeta['generosa']),
            ctrl.Rule(self.tempo_atendimento['demorado'], 
                     self.gorjeta['sem_gorjeta']),
            ctrl.Rule(self.tempo_atendimento['rapido'] | self.tempo_atendimento['mediano'], 
                     self.gorjeta['media']),
            ctrl.Rule(self.qualidade_refeicao['normal'] & self.qualidade_servico['aceitavel'], 
                     self.gorjeta['media'])
        ]
        
        self.sistema_controle = ctrl.ControlSystem(self.regras)
        self.sistema = ctrl.ControlSystemSimulation(self.sistema_controle)

    def mostrar_menu(self):
        print("\n" + "="*50)
        print("CALCULADORA DE GORJETAS COM LOGICA FUZZY".center(50))
        print("="*50)
        print("\n1. Calcular nova gorjeta")
        print("2. Visualizar conjuntos fuzzy")
        print("3. Ver histórico de cálculos")
        print("4. Ver explicação das regras")
        print("5. Sair")
        return input("\nEscolha uma opção (1-5): ")

    def obter_entrada_valida(self, mensagem, min_valor, max_valor):
        while True:
            try:
                valor = float(input(mensagem))
                if min_valor <= valor <= max_valor:
                    return valor
                print(f"Por favor, insira um valor entre {min_valor} e {max_valor}")
            except ValueError:
                print("Por favor, insira um número válido")

    def calcular_gorjeta(self):
        print("\n--- Cálculo de Gorjeta ---")
        
        # pegar entradas
        qualidade_ref = self.obter_entrada_valida(
            "Qualidade da refeição (0-10): ", 0, 10)
        qualidade_serv = self.obter_entrada_valida(
            "Qualidade do serviço (0-10): ", 0, 10)
        tempo_atend = self.obter_entrada_valida(
            "Tempo de atendimento (minutos, 0-60): ", 0, 60)
        valor_conta = self.obter_entrada_valida(
            "Valor da conta (R$): ", 0, 100000)

        # tips 
        self.sistema.input['qualidade_refeicao'] = qualidade_ref
        self.sistema.input['qualidade_servico'] = qualidade_serv
        self.sistema.input['tempo_atendimento'] = tempo_atend
        
        try:
            self.sistema.compute()
            porcentagem_gorjeta = self.sistema.output['gorjeta']
            valor_gorjeta = (porcentagem_gorjeta / 100) * valor_conta
            
            # salva historico
            resultado = {
                'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'qualidade_refeicao': qualidade_ref,
                'qualidade_servico': qualidade_serv,
                'tempo_atendimento': tempo_atend,
                'valor_conta': valor_conta,
                'porcentagem_gorjeta': porcentagem_gorjeta,
                'valor_gorjeta': valor_gorjeta
            }
            self.historico.append(resultado)
            self.salvar_historico()
            
            print("\n=== Resultado do Cálculo ===")
            print(f"Porcentagem de gorjeta sugerida: {porcentagem_gorjeta:.2f}%")
            print(f"Valor da gorjeta: R$ {valor_gorjeta:.2f}")
            print(f"Valor total a pagar: R$ {(valor_conta + valor_gorjeta):.2f}")
            
            input("\nPressione Enter para continuar...")
            
        except:
            print("\nErro no cálculo da gorjeta.")

    def visualizar_conjuntos(self):
        print("\nGerando visualização dos conjuntos fuzzy...")
        
        # config do estilo
        plt.style.use('seaborn-v0_8')
        
        # cria figura e subplot
        fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
        
        # plota quantidade refeicao 
        ax0.plot(self.qualidade_refeicao.universe, fuzz.trimf(self.qualidade_refeicao.universe, [0, 0, 5]), 'b', linewidth=1.5, label='Insossa')
        ax0.plot(self.qualidade_refeicao.universe, fuzz.trimf(self.qualidade_refeicao.universe, [0, 5, 10]), 'g', linewidth=1.5, label='Normal')
        ax0.plot(self.qualidade_refeicao.universe, fuzz.trimf(self.qualidade_refeicao.universe, [5, 10, 10]), 'r', linewidth=1.5, label='Saborosa')
        ax0.set_title('Qualidade da Refeição')
        ax0.legend()
        
        # plota qualidade do servico 
        ax1.plot(self.qualidade_servico.universe, fuzz.trimf(self.qualidade_servico.universe, [0, 0, 5]), 'b', linewidth=1.5, label='Ruim')
        ax1.plot(self.qualidade_servico.universe, fuzz.trimf(self.qualidade_servico.universe, [0, 5, 10]), 'g', linewidth=1.5, label='Aceitável')
        ax1.plot(self.qualidade_servico.universe, fuzz.trimf(self.qualidade_servico.universe, [5, 10, 10]), 'r', linewidth=1.5, label='Excelente')
        ax1.set_title('Qualidade do Serviço')
        ax1.legend()
        
        # plota tempo atendimento
        ax2.plot(self.tempo_atendimento.universe, fuzz.trimf(self.tempo_atendimento.universe, [0, 0, 20]), 'b', linewidth=1.5, label='Rápido')
        ax2.plot(self.tempo_atendimento.universe, fuzz.trimf(self.tempo_atendimento.universe, [10, 25, 40]), 'g', linewidth=1.5, label='Mediano')
        ax2.plot(self.tempo_atendimento.universe, fuzz.trimf(self.tempo_atendimento.universe, [30, 60, 60]), 'r', linewidth=1.5, label='Demorado')
        ax2.set_title('Tempo de Atendimento')
        ax2.legend()
        
        # plota gorjeta
        ax3.plot(self.gorjeta.universe, fuzz.trimf(self.gorjeta.universe, [0, 0, 5]), 'b', linewidth=1.5, label='Sem Gorjeta')
        ax3.plot(self.gorjeta.universe, fuzz.trimf(self.gorjeta.universe, [0, 10, 15]), 'g', linewidth=1.5, label='Pouca')
        ax3.plot(self.gorjeta.universe, fuzz.trimf(self.gorjeta.universe, [10, 15, 20]), 'y', linewidth=1.5, label='Média')
        ax3.plot(self.gorjeta.universe, fuzz.trimf(self.gorjeta.universe, [15, 30, 30]), 'r', linewidth=1.5, label='Generosa')
        ax3.set_title('Gorjeta')
        ax3.legend()
        
        # ajusta layout
        for ax in (ax0, ax1, ax2, ax3):
            ax.grid(True)
            ax.set_ylim([-0.1, 1.1])
        
        plt.tight_layout()
        plt.show()

    def mostrar_historico(self):
        if not self.historico:
            print("\nNenhum cálculo registrado no histórico.")
            return

        headers = ["Data", "Refeição", "Serviço", "Tempo", "Valor", "Gorjeta %", "Gorjeta R$"]
        dados = [[
            h['data'],
            f"{h['qualidade_refeicao']:.1f}",
            f"{h['qualidade_servico']:.1f}",
            f"{h['tempo_atendimento']:.1f}",
            f"R$ {h['valor_conta']:.2f}",
            f"{h['porcentagem_gorjeta']:.2f}%",
            f"R$ {h['valor_gorjeta']:.2f}"
        ] for h in self.historico]
        
        print("\n=== Histórico de Cálculos ===")
        print(tabulate(dados, headers=headers, tablefmt="grid"))
        input("\nPressione Enter para continuar...")

    def mostrar_explicacao_regras(self):
        print("\n=== Explicação das Regras do Sistema ===")
        regras = [
            "1. Se a refeição estiver insossa E o serviço ruim → gorjeta pouca",
            "2. Se a refeição estiver saborosa E o serviço excelente → gorjeta generosa",
            "3. Se o tempo de atendimento for demorado → sem gorjeta",
            "4. Se o tempo de atendimento for rápido OU mediano → gorjeta média",
            "5. Se a refeição estiver normal E o serviço aceitável → gorjeta média"
        ]
        
        for regra in regras:
            print(regra)
            time.sleep(1) 
        
        input("\nPressione Enter para continuar...")

    def carregar_historico(self):
        try:
            if os.path.exists('historico_gorjetas.json'):
                with open('historico_gorjetas.json', 'r') as f:
                    self.historico = json.load(f)
        except:
            self.historico = []

    def salvar_historico(self):
        try:
            with open('historico_gorjetas.json', 'w') as f:
                json.dump(self.historico, f)
        except:
            print("Erro ao salvar histórico.")

    def executar(self):
        while True:
            opcao = self.mostrar_menu()
            
            if opcao == '1':
                self.calcular_gorjeta()
            elif opcao == '2':
                self.visualizar_conjuntos()
            elif opcao == '3':
                self.mostrar_historico()
            elif opcao == '4':
                self.mostrar_explicacao_regras()
            elif opcao == '5':
                print("\nObrigado por usar a calculadora de gorjetas!")
                break
            else:
                print("\nOpção inválida. Por favor, tente novamente.")

if __name__ == "__main__":
    calculadora = CalculadoraGorjeta()
    calculadora.executar()