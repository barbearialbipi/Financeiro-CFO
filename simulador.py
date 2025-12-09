import streamlit as st
import pandas as pd
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Master CFO Barbearia", layout="wide")

def main():
    st.title("💈 Master CFO: Sistema de Gestão Financeira")
    st.markdown("---")

    # ==========================================
    # 1. SIDEBAR: DADOS DO PROJETO
    # ==========================================
    st.sidebar.header("1. Investimento (CAPEX)")
    investimento_inicial = st.sidebar.number_input(
        "Investimento Total (R$)", value=15000.0, step=500.0, help="Obras, Equipamentos, Mobília"
    )

    st.sidebar.header("2. Custos Fixos (OPEX)")
    with st.sidebar.expander("Detalhar Custos Mensais", expanded=False):
        aluguel = st.number_input("Aluguel", value=2500.0)
        energia = st.number_input("Utilidades (Luz/Água/Net)", value=550.0)
        folha = st.number_input("Folha Adm/Recepção", value=1800.0)
        mkt = st.number_input("Marketing/Sistemas", value=450.0)
        custos_fixos_totais = aluguel + energia + folha + mkt
        st.write(f"**Total Fixo: R$ {custos_fixos_totais:.2f}**")

    st.sidebar.header("3. Premissas Financeiras")
    meses_analise = st.sidebar.slider("Horizonte (Meses)", 12, 60, 24)
    tma_anual = st.sidebar.number_input("Taxa Mínima de Atratividade (% a.a.)", value=12.0)
    tma_mensal = (tma_anual / 100) / 12

    st.sidebar.header("4. Volume de Vendas")
    clientes_dia = st.sidebar.number_input("Média Clientes/Dia", value=15)
    dias_mes = st.sidebar.number_input("Dias Trabalhados/Mês", value=24)
    total_atendimentos = clientes_dia * dias_mes

    # ==========================================
    # 2. ENGENHARIA DE MENU (TABELA DE MIX)
    # ==========================================
    st.subheader("🛠️ Engenharia de Menu (Mix de Produtos)")
    st.info("Ajuste abaixo o **Preço**, o **Custo Variável** e a **Popularidade (Mix)** de cada serviço.")

    # Seus serviços reais
    dados_servicos = {
        "Serviço": [
            "Tradicional", "Social", "Degradê", "Navalhado", 
            "Abordagem Visagismo", "Consultoria Visagismo"
        ],
        "Preço (R$)": [17.00, 20.00, 25.00, 27.00, 45.00, 65.00],
        "Custo Var. (R$)": [8.00, 9.00, 12.00, 13.00, 20.00, 25.00], 
        "Mix %": [10, 20, 40, 20, 5, 5] 
    }

    df_mix = pd.DataFrame(dados_servicos)

    col_tabela, col_resumo_mix = st.columns([2, 1])

    with col_tabela:
        df_editado = st.data_editor(
            df_mix,
            column_config={
                "Preço (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Custo Var. (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Mix %": st.column_config.NumberColumn(format="%d %%", min_value=0, max_value=100)
            },
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True
        )

    # Validação do Mix
    total_mix = df_editado["Mix %"].sum()
    if total_mix != 100:
        st.error(f"⚠️ A soma do Mix está em {total_mix}%. Ajuste para dar exatamente 100%.")
        st.stop()

    # Cálculo do Ticket Médio Ponderado
    df_editado["Receita Ponderada"] = df_editado["Preço (R$)"] * (df_editado["Mix %"] / 100)
    df_editado["Custo Ponderado"] = df_editado["Custo Var. (R$)"] * (df_editado["Mix %"] / 100)
    
    ticket_medio = df_editado["Receita Ponderada"].sum()
    custo_var_medio = df_editado["Custo Ponderado"].sum()
    margem_contrib_unitaria = ticket_medio - custo_var_medio

    with col_resumo_mix:
        st.write("RESUMO DO MIX:")
        st.metric("Ticket Médio Real", f"R$ {ticket_medio:.2f}")
        st.metric("Margem por Cliente", f"R$ {margem_contrib_unitaria:.2f}")

    # ==========================================
    # 3. MOTOR DE CÁLCULO FINANCEIRO
    # ==========================================
    
    # 1. Operacional
    receita_bruta = total_atendimentos * ticket_medio
    custo_var_total = total_atendimentos * custo_var_medio
    lucro_operacional = receita_bruta - custo_var_total - custos_fixos_totais

    # 2. Ponto de Equilíbrio e Margem de Segurança
    pe_qtd = custos_fixos_totais / margem_contrib_unitaria if margem_contrib_unitaria > 0 else 0
    pe_receita = pe_qtd * ticket_medio
    
    if total_atendimentos > 0:
        margem_seguranca = (total_atendimentos - pe_qtd) / total_atendimentos * 100
    else:
        margem_seguranca = -100

    # 3. Fluxo de Caixa (VPL, Payback, TIR)
    fluxo_lista = [-investimento_inicial]
    saldo_acumulado = -investimento_inicial
    vpl = -investimento_inicial
    payback_mes = None
    dados_grafico = []

    for mes in range(1, meses_analise + 1):
        fluxo_lista.append(lucro_operacional)
        saldo_anterior = saldo_acumulado
        saldo_acumulado += lucro_operacional
        
        # Detecta Payback
        if saldo_anterior < 0 and saldo_acumulado >= 0 and payback_mes is None:
            payback_mes = mes
            
        # Calcula VPL
        vp = lucro_operacional / ((1 + tma_mensal) ** mes)
        vpl += vp
        
        dados_grafico.append({"Mês": mes, "Saldo Acumulado": saldo_acumulado})

    df_grafico = pd.DataFrame(dados_grafico)

    # 4. Indicadores Avançados (TIR e IL)
    try:
        tir_mensal = np.irr(fluxo_lista)
        if pd.isna(tir_mensal): tir_mensal = 0
    except:
        tir_mensal = 0
    tir_anual = ((1 + tir_mensal) ** 12) - 1

    roi = ((saldo_acumulado + investimento_inicial) / investimento_inicial * 100) if investimento_inicial > 0 else 0
    indice_lucratividade = (vpl + investimento_inicial) / investimento_inicial if investimento_inicial > 0 else 0

    # ==========================================
    # 4. DASHBOARD EXECUTIVO (CFO VIEW)
    # ==========================================
    st.divider()
    st.header("📊 Painel de Controle Financeiro")

    # LINHA 1: VIABILIDADE DO INVESTIMENTO
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("VPL (Riqueza)", f"R$ {vpl:,.2f}", delta="Viável" if vpl > 0 else "Inviável")
    col2.metric("TIR (Retorno Real)", f"{tir_anual*100:.1f}% a.a.", delta=f"Meta: {tma_anual}%")
    col3.metric("Payback", f"{payback_mes} meses" if payback_mes else "Nunca", delta_color="inverse")
    col4.metric("ROI Total", f"{roi:.1f}%")
    col5.metric("Índice Lucratividade", f"{indice_lucratividade:.2f}x", help="Para cada 1 real, voltam X reais.")

    st.markdown("---")

    # LINHA 2: SAÚDE MENSAL E RISCO
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Lucro Mensal", f"R$ {lucro_operacional:,.2f}")
    kpi2.metric("Ponto de Equilíbrio", f"{int(pe_qtd)} clientes")
    
    # Lógica de cor da Margem de Segurança
    if margem_seguranca < 0: cor_ms = "inverse"
    elif margem_seguranca < 20: cor_ms = "off"
    else: cor_ms = "normal"
    
    kpi3.metric("Margem de Segurança", f"{margem_seguranca:.1f}%", delta="Risco", delta_color=cor_ms)
    kpi4.metric("Faturamento Bruto", f"R$ {receita_bruta:,.2f}")

    # GRÁFICOS E AVAL
    tab1, tab2 = st.tabs(["📈 Curva de Investimento", "🤖 Avaliação do Consultor"])

    with tab1:
        st.line_chart(df_grafico, x="Mês", y="Saldo Acumulado")
        st.caption("A linha mostra a evolução do seu dinheiro no bolso. Quando cruza o zero, o investimento está pago.")

    with tab2:
        st.subheader("Veredito Final")
        
        # Cenário 1: Prejuízo Operacional
        if lucro_operacional < 0:
            st.error(f"🛑 **INVIÁVEL:** Você perde R$ {abs(lucro_operacional):.2f} por mês. O mix de produtos atual não paga os custos fixos.")
        
        # Cenário 2: Lucro, mas VPL Negativo
        elif vpl < 0:
            st.warning(f"⚠️ **CUIDADO:** O projeto dá lucro, mas financeiramente não compensa o risco. O VPL é negativo. Melhor deixar o dinheiro aplicado.")
            
        # Cenário 3: Sucesso
        else:
            st.success(f"✅ **APROVADO:** Projeto Excelente!")
            st.markdown(f"""
            * **Tempo de Retorno:** {payback_mes} meses (Rápido? Avalie se cabe no seu bolso).
            * **Rentabilidade:** A TIR é de **{tir_anual*100:.1f}%**, superando sua meta de {tma_anual}%.
            * **Eficiência:** Para cada 1 real investido, você gera **{indice_lucratividade:.2f}** reais de riqueza ajustada.
            """)
            
            if margem_seguranca < 15:
                st.info("💡 **Dica:** Sua Margem de Segurança está baixa (<15%). Tente reduzir custos fixos para sofrer menos em meses fracos.")

if __name__ == "__main__":
    main()
