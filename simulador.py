import streamlit as st
import pandas as pd
import numpy as np # Biblioteca padrão de matemática para calcular a TIR

# Configuração da Página
st.set_page_config(page_title="CFO Barbearia System", layout="wide")

# Função auxiliar para calcular TIR (IRR) sem depender de bibliotecas financeiras externas complexas
def calcular_tir(fluxos):
    try:
        # np.irr foi depreciado, usa-se numpy_financial.irr, mas para garantir que rode
        # em qualquer lugar, usaremos a implementação clássica ou aproximação.
        # Aqui usaremos a função roots do numpy que é padrão.
        # A TIR é a taxa que faz o VPL ser zero.
        tir = np.irr(fluxos) 
        return tir * 100
    except:
        return 0.0

def main():
    st.title("💈 CFO System: Análise de Investimento & Orçamento")
    st.markdown("---")

    # ==========================================
    # 1. SIDEBAR: O ORÇAMENTO
    # ==========================================
    st.sidebar.header("1. CAPEX (Investimento)")
    investimento_inicial = st.sidebar.number_input(
        "Valor do Investimento (R$)", value=15000.0, step=500.0
    )

    st.sidebar.header("2. OPEX (Custos Fixos)")
    with st.sidebar.expander("Detalhar Custos Fixos", expanded=False):
        aluguel = st.number_input("Aluguel", value=2500.0)
        energia = st.number_input("Utilidades (Luz/Água/Net)", value=550.0)
        folha = st.number_input("Folha Adm/Recepção", value=1800.0)
        mkt = st.number_input("Marketing/Sistemas", value=450.0)
        custos_fixos_totais = aluguel + energia + folha + mkt
        st.write(f"**Total Fixo Mensal: R$ {custos_fixos_totais:.2f}**")

    st.sidebar.header("3. Premissas Financeiras")
    meses_analise = st.sidebar.slider("Horizonte de Análise (Meses)", 12, 60, 24)
    tma_anual = st.sidebar.number_input("TMA - Taxa Mínima de Atratividade (% a.a.)", value=12.0, help="Quanto seu dinheiro renderia num investimento seguro (CDB/Tesouro)?")
    tma_mensal = (tma_anual / 100) / 12

    st.sidebar.header("4. Engenharia de Receita")
    clientes_dia = st.sidebar.number_input("Clientes/Dia (Média)", value=15)
    dias_mes = st.sidebar.number_input("Dias Funcionamento/Mês", value=24)
    total_atendimentos = clientes_dia * dias_mes

    st.subheader("Mix de Produtos")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("Básico")
        pA = st.number_input("Preço", 40.0, key="pA")
        cA = st.number_input("Custo Var.", 15.0, key="cA")
        mA = st.slider("% Vol.", 0, 100, 50, key="mA")/100
    with c2:
        st.warning("Interm.")
        pB = st.number_input("Preço", 60.0, key="pB")
        cB = st.number_input("Custo Var.", 25.0, key="cB")
        mB = st.slider("% Vol.", 0, 100, 30, key="mB")/100
    with c3:
        st.success("Premium")
        pC = st.number_input("Preço", 90.0, key="pC")
        cC = st.number_input("Custo Var.", 40.0, key="cC")
        mC = max(0.0, 1.0 - (mA + mB))
        st.metric("% Vol.", f"{mC*100:.0f}%")

    # ==========================================
    # 2. MOTOR DE CÁLCULO
    # ==========================================
    
    # Médias Ponderadas
    ticket_medio = (pA*mA) + (pB*mB) + (pC*mC)
    custo_var_medio = (cA*mA) + (cB*mB) + (cC*mC)
    margem_contrib = ticket_medio - custo_var_medio

    # Resultados Operacionais
    receita_bruta = total_atendimentos * ticket_medio
    custo_var_total = total_atendimentos * custo_var_medio
    lucro_operacional = receita_bruta - custo_var_total - custos_fixos_totais
    
    # Ponto de Equilíbrio
    ponto_equilibrio_qtd = custos_fixos_totais / margem_contrib if margem_contrib > 0 else 0
    ponto_equilibrio_receita = ponto_equilibrio_qtd * ticket_medio

    # Margem de Segurança
    if total_atendimentos > 0:
        margem_seguranca_pct = (total_atendimentos - ponto_equilibrio_qtd) / total_atendimentos * 100
    else:
        margem_seguranca_pct = -100

    # Fluxo de Caixa e VPL
    fluxo_caixa_lista = [-investimento_inicial] # O fluxo começa com o gasto no tempo 0
    saldo = -investimento_inicial
    vpl = -investimento_inicial
    dados_grafico = []
    payback_mes = None

    for m in range(1, meses_analise + 1):
        fluxo_caixa_lista.append(lucro_operacional) # Adiciona fluxo para cálculo da TIR
        
        saldo_ant = saldo
        saldo += lucro_operacional
        
        # Payback Simples
        if saldo_ant < 0 and saldo >= 0 and payback_mes is None:
            payback_mes = m
            
        # VPL
        vp = lucro_operacional / ((1 + tma_mensal)**m)
        vpl += vp
        
        dados_grafico.append({"Mês": m, "Saldo Acumulado": saldo, "Fluxo Mensal": lucro_operacional})

    df = pd.DataFrame(dados_grafico)

    # TIR (Taxa Interna de Retorno)
    # Nota: np.irr retorna a taxa periódica (mensal neste caso)
    try:
        tir_mensal = np.irr(fluxo_caixa_lista)
        if pd.isna(tir_mensal): tir_mensal = 0
    except:
        tir_mensal = 0
    
    tir_anual = ((1 + tir_mensal) ** 12) - 1 # Anualizando a taxa

    # Índice de Lucratividade
    indice_lucratividade = (vpl + investimento_inicial) / investimento_inicial if investimento_inicial > 0 else 0

    # ==========================================
    # 3. DASHBOARD EXECUTIVO
    # ==========================================
    
    st.divider()

    # --- LINHA 1: INDICADORES DE VIABILIDADE (INVESTIMENTO) ---
    st.subheader("💰 Viabilidade do Investimento")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("VPL (Riqueza Gerada)", f"R$ {vpl:,.2f}", 
                delta="Viável" if vpl > 0 else "Inviável")
    
    col2.metric("TIR (Rentabilidade Real)", f"{tir_anual*100:.1f}% ao ano",
                delta=f"Meta: {tma_anual}%", delta_color="normal")
    
    col3.metric("Payback (Retorno)", f"{payback_mes} meses" if payback_mes else "Não recupera",
                delta="Tempo p/ pagar" if payback_mes else "Risco Alto", delta_color="inverse")
    
    col4.metric("Índice Lucratividade", f"{indice_lucratividade:.2f}x",
                help="Para cada R$ 1,00 investido, quanto retorna de valor presente.")

    st.markdown("---")

    # --- LINHA 2: SAÚDE OPERACIONAL (ORÇAMENTO) ---
    st.subheader("⚙️ Saúde Operacional e Risco")
    kpi1, kpi2, kpi3 = st.columns(3)

    kpi1.metric("Lucro Líquido Mensal", f"R$ {lucro_operacional:,.2f}")
    
    kpi2.metric("Ponto de Equilíbrio", f"{int(ponto_equilibrio_qtd)} clientes/mês",
                help=f"Você precisa faturar R$ {ponto_equilibrio_receita:,.2f} para empatar.")
    
    # Lógica de cor da Margem de Segurança
    cor_margem = "off"
    if margem_seguranca_pct < 0: cor_margem = "inverse" # Vermelho (Prejuízo)
    elif margem_seguranca_pct < 20: cor_margem = "off"  # Cinza/Amarelo (Risco)
    else: cor_margem = "normal"                         # Verde (Seguro)

    kpi3.metric("Margem de Segurança", f"{margem_seguranca_pct:.1f}%",
                delta="Distância do Prejuízo", delta_color=cor_margem,
                help="Quanto suas vendas podem cair antes de você ter prejuízo.")

    # --- GRÁFICOS E TABELAS ---
    st.markdown("---")
    tab1, tab2 = st.tabs(["📉 Análise Gráfica", "📋 DRE Projetado"])
    
    with tab1:
        st.caption("A linha azul mostra o dinheiro no bolso acumulado ao longo do tempo.")
        st.line_chart(df, x="Mês", y="Saldo Acumulado")
        if margem_seguranca_pct > 0:
            st.success(f"Dica de Gestão: Você tem uma gordura de {margem_seguranca_pct:.1f}% na operação. Isso permite investir em promoções sem entrar no vermelho.")
        else:
            st.error("Alerta de Gestão: Você está operando abaixo ou muito próximo do Ponto de Equilíbrio. Priorize redução de custos fixos urgentemente.")

    with tab2:
        st.write("Detalhamento mês a mês:")
        st.dataframe(df.style.format({"Saldo Acumulado": "R$ {:.2f}", "Fluxo Mensal": "R$ {:.2f}"}))

if __name__ == "__main__":
    main()
