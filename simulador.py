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
        "Investimento Total (R$)", value=15000.0, step=500.0
    )

    st.sidebar.header("2. Custos Fixos (OPEX)")
    with st.sidebar.expander("Detalhar Custos Mensais", expanded=False):
        aluguel = st.number_input("Aluguel", value=2500.0)
        energia = st.number_input("Utilidades (Luz/Água/Net)", value=550.0)
        folha = st.number_input("Folha Adm/Recepção", value=1800.0)
        mkt = st.number_input("Marketing/Sistemas", value=450.0)
        custos_fixos_totais = aluguel + energia + folha + mkt
        st.write(f"**Total Fixo: R$ {custos_fixos_totais:.2f}**")

    # SEÇÃO: COMISSÕES
    st.sidebar.header("3. Equipe e Comissões")
    
    col_dono, col_equipe = st.sidebar.columns(2)
    comissao_dono = col_dono.number_input("% Com. Dono", value=81.46, step=0.1) / 100
    comissao_equipe = col_equipe.number_input("% Com. Equipe", value=40.00, step=0.1) / 100
    
    share_dono = st.sidebar.slider("% Atendimentos feitos pelo Dono", 0, 100, 30) / 100
    share_equipe = 1.0 - share_dono
    
    comissao_media_ponderada = (comissao_dono * share_dono) + (comissao_equipe * share_equipe)
    st.sidebar.metric("Custo Médio de Comissão", f"{comissao_media_ponderada*100:.2f}%")

    st.sidebar.header("4. Premissas Financeiras")
    meses_analise = st.sidebar.slider("Horizonte (Meses)", 12, 60, 24)
    tma_anual = st.sidebar.number_input("Taxa Mínima (Selic % a.a.)", value=12.0)
    tma_mensal = (tma_anual / 100) / 12

    st.sidebar.header("5. Volume de Vendas")
    clientes_dia = st.sidebar.number_input("Média Clientes/Dia", value=15)
    dias_mes = st.sidebar.number_input("Dias Trabalhados/Mês", value=24)
    total_atendimentos = clientes_dia * dias_mes

    # ==========================================
    # 2. ENGENHARIA DE MENU (TABELA DE MIX)
    # ==========================================
    st.subheader("🛠️ Engenharia de Menu (Produtos e Mix)")

    dados_servicos = {
        "Serviço": [
            "Tradicional", "Social", "Degradê", "Navalhado", 
            "Abordagem Visagismo", "Consultoria Visagismo"
        ],
        "Preço (R$)": [17.00, 20.00, 25.00, 27.00, 45.00, 65.00],
        "Custo Produtos (R$)": [2.00, 2.50, 3.00, 4.00, 5.00, 5.00], 
        "Mix %": [10, 20, 40, 20, 5, 5] 
    }

    df_mix = pd.DataFrame(dados_servicos)

    col_tabela, col_resumo_mix = st.columns([2, 1])

    with col_tabela:
        df_editado = st.data_editor(
            df_mix,
            column_config={
                "Preço (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Custo Produtos (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
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

    # ==========================================
    # 3. CÁLCULOS E MARGEM DE CONTRIBUIÇÃO
    # ==========================================
    
    # Custos Unitários
    df_editado["Custo Comissão (R$)"] = df_editado["Preço (R$)"] * comissao_media_ponderada
    df_editado["Custo Total Unitário"] = df_editado["Custo Produtos (R$)"] + df_editado["Custo Comissão (R$)"]
    
    # Médias Ponderadas
    df_editado["Receita Pond"] = df_editado["Preço (R$)"] * (df_editado["Mix %"] / 100)
    df_editado["Custo Total Pond"] = df_editado["Custo Total Unitário"] * (df_editado["Mix %"] / 100)
    
    ticket_medio = df_editado["Receita Pond"].sum()
    custo_var_medio = df_editado["Custo Total Pond"].sum()
    
    # --- AQUI ESTÁ ELA: MARGEM DE CONTRIBUIÇÃO UNITÁRIA ---
    margem_contrib_unitaria = ticket_medio - custo_var_medio
    margem_contrib_pct = (margem_contrib_unitaria / ticket_medio) * 100 if ticket_medio > 0 else 0

    with col_resumo_mix:
        st.write("🔎 RAIO-X DO CORTE:")
        st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        st.metric("Custo Variável", f"R$ {custo_var_medio:.2f}", delta="- (Prod + Comissões)", delta_color="inverse")
        
        # DESTAQUE NA MARGEM UNITÁRIA
        st.metric("Margem Contrib. (Unit)", f"R$ {margem_contrib_unitaria:.2f}", 
                  delta=f"{margem_contrib_pct:.1f}% do valor", delta_color="normal")
        st.caption("É o valor limpo que sobra de cada cliente para pagar as contas.")

    # ==========================================
    # 4. MOTOR FINANCEIRO
    # ==========================================
    
    receita_bruta = total_atendimentos * ticket_medio
    custo_var_total = total_atendimentos * custo_var_medio
    
    # --- MARGEM DE CONTRIBUIÇÃO TOTAL ---
    margem_contrib_total = receita_bruta - custo_var_total
    
    lucro_operacional = margem_contrib_total - custos_fixos_totais

    pe_qtd = custos_fixos_totais / margem_contrib_unitaria if margem_contrib_unitaria > 0 else 0
    margem_seguranca = (total_atendimentos - pe_qtd) / total_atendimentos * 100 if total_atendimentos > 0 else -100

    fluxo_lista = [-investimento_inicial]
    saldo_acumulado = -investimento_inicial
    vpl = -investimento_inicial
    payback_mes = None
    dados_grafico = []

    for mes in range(1, meses_analise + 1):
        fluxo_lista.append(lucro_operacional)
        saldo_anterior = saldo_acumulado
        saldo_acumulado += lucro_operacional
        if saldo_anterior < 0 and saldo_acumulado >= 0 and payback_mes is None: payback_mes = mes
        vp = lucro_operacional / ((1 + tma_mensal) ** mes)
        vpl += vp
        dados_grafico.append({"Mês": mes, "Saldo Acumulado": saldo_acumulado})

    df_grafico = pd.DataFrame(dados_grafico)

    try:
        tir_mensal = np.irr(fluxo_lista)
        if pd.isna(tir_mensal): tir_mensal = 0
    except:
        tir_mensal = 0
    tir_anual = ((1 + tir_mensal) ** 12) - 1
    
    roi = ((saldo_acumulado + investimento_inicial) / investimento_inicial * 100) if investimento_inicial > 0 else 0
    indice_lucratividade = (vpl + investimento_inicial) / investimento_inicial if investimento_inicial > 0 else 0

    # ==========================================
    # 5. DASHBOARD FINAL
    # ==========================================
    st.divider()
    st.header("📊 Painel de Controle")

    # LINHA 1: INDICADORES ESTRATÉGICOS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento Bruto", f"R$ {receita_bruta:,.2f}")
    
    # AQUI ESTÁ A MARGEM TOTAL
    c2.metric("Margem Contrib. Total", f"R$ {margem_contrib_total:,.2f}", 
              help="Valor total que sobrou para pagar os Custos Fixos.",
              delta="Dinheiro Limpo")
    
    c3.metric("Custos Fixos", f"R$ {custos_fixos_totais:,.2f}", delta_color="inverse")
    c4.metric("Lucro Líquido", f"R$ {lucro_operacional:,.2f}", 
              delta="Prejuízo" if lucro_operacional < 0 else "Lucro", 
              delta_color="normal" if lucro_operacional > 0 else "inverse")

    st.markdown("---")
    
    # LINHA 2: VIABILIDADE E RISCO
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ponto de Equilíbrio", f"{int(pe_qtd)} cortes", help="Quantos cortes para pagar os custos fixos.")
    k2.metric("VPL (Riqueza)", f"R$ {vpl:,.2f}")
    k3.metric("Payback", f"{payback_mes} meses" if payback_mes else "Nunca")
    
    cor_ms = "normal" if margem_seguranca > 20 else ("off" if margem_seguranca > 0 else "inverse")
    k4.metric("Margem de Segurança", f"{margem_seguranca:.1f}%", delta_color=cor_ms)

    # GRÁFICOS
    tab1, tab2 = st.tabs(["📈 Curva Financeira", "📋 Avaliação"])
    with tab1:
        st.line_chart(df_grafico, x="Mês", y="Saldo Acumulado")
    with tab2:
        st.write(f"**Análise da Margem:** Sua Margem de Contribuição é de **{margem_contrib_pct:.1f}%**.")
        if margem_contrib_pct < 30:
            st.error("Sua margem está abaixo de 30%. O custo variável (comissões/produtos) está muito alto. É difícil pagar os custos fixos assim.")
        elif margem_contrib_pct > 50:
            st.success("Sua margem está excelente (acima de 50%). Você tem uma operação muito saudável.")
        else:
            st.warning("Sua margem está na média (entre 30% e 50%). Controle bem os custos fixos.")

        if lucro_operacional > 0:
            st.success(f"O projeto é VIÁVEL. ROI de {roi:.1f}% ao final do período.")
        else:
            st.error("O projeto opera no PREJUÍZO.")

if __name__ == "__main__":
    main()
