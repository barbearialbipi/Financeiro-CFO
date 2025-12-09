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
    
    share_dono = st.sidebar.slider("% Atendimentos do Dono", 0, 100, 30) / 100
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
    st.info("💡 Dica: Para adicionar um novo serviço, clique na última linha vazia ou no botão '+' abaixo da tabela.")

    # Dados iniciais (Note que usei floats no Mix para permitir decimais)
    dados_servicos = {
        "Serviço": [
            "Tradicional", "Social", "Degradê", "Navalhado", 
            "Abordagem Visagismo", "Consultoria Visagismo"
        ],
        "Preço (R$)": [17.00, 20.00, 25.00, 27.00, 45.00, 65.00],
        "Custo Produtos (R$)": [2.00, 2.50, 3.00, 4.00, 5.00, 5.00], 
        "Mix %": [10.0, 20.0, 40.0, 20.0, 5.0, 5.0] # Floats (com ponto)
    }

    df_mix = pd.DataFrame(dados_servicos)

    col_tabela, col_resumo_mix = st.columns([2, 1])

    with col_tabela:
        df_editado = st.data_editor(
            df_mix,
            column_config={
                "Preço (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Custo Produtos (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                # AQUI ESTÁ A MUDANÇA PARA DECIMAIS
                "Mix %": st.column_config.NumberColumn(
                    format="%.2f %%", # Aceita 2 casas decimais (Ex: 12.50%)
                    step=0.1,        # Permite subir de 0.1 em 0.1
                    min_value=0.0,
                    max_value=100.0
                )
            },
            hide_index=True,
            num_rows="dynamic", # ISSO PERMITE ADICIONAR LINHAS
            use_container_width=True
        )

    # Validação do Mix (Usando margem de erro pequena para decimais)
    total_mix = df_editado["Mix %"].sum()
    # Se a diferença for maior que 0.1, dá erro (para evitar erros de arredondamento tipo 99.99999)
    if abs(total_mix - 100.0) > 0.1:
        st.error(f"⚠️ A soma do Mix está em {total_mix:.2f}%. Precisa ser exatamente 100%.")
        st.stop()

    # ==========================================
    # 3. CÁLCULOS E MARGEM DE CONTRIBUIÇÃO
    # ==========================================
    
    df_editado["Custo Comissão (R$)"] = df_editado["Preço (R$)"] * comissao_media_ponderada
    df_editado["Custo Total Unitário"] = df_editado["Custo Produtos (R$)"] + df_editado["Custo Comissão (R$)"]
    
    df_editado["Receita Pond"] = df_editado["Preço (R$)"] * (df_editado["Mix %"] / 100)
    df_editado["Custo Total Pond"] = df_editado["Custo Total Unitário"] * (df_editado["Mix %"] / 100)
    
    ticket_medio = df_editado["Receita Pond"].sum()
    custo_var_medio = df_editado["Custo Total Pond"].sum()
    margem_contrib_unitaria = ticket_medio - custo_var_medio
    margem_contrib_pct = (margem_contrib_unitaria / ticket_medio) * 100 if ticket_medio > 0 else 0

    with col_resumo_mix:
        st.write("🔎 RAIO-X DO CORTE:")
        st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
        st.metric("Custo Variável", f"R$ {custo_var_medio:.2f}", delta="- (Prod + Comissões)", delta_color="inverse")
        st.metric("Margem Contrib. (Unit)", f"R$ {margem_contrib_unitaria:.2f}", 
                  delta=f"{margem_contrib_pct:.1f}%", delta_color="normal")

    # ==========================================
    # 4. MOTOR FINANCEIRO
    # ==========================================
    
    receita_bruta = total_atendimentos * ticket_medio
    custo_var_total = total_atendimentos * custo_var_medio
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento Bruto", f"R$ {receita_bruta:,.2f}")
    c2.metric("Margem Contrib. Total", f"R$ {margem_contrib_total:,.2f}", delta="Dinheiro Limpo")
    c3.metric("Custos Fixos", f"R$ {custos_fixos_totais:,.2f}", delta_color="inverse")
    c4.metric("Lucro Líquido", f"R$ {lucro_operacional:,.2f}", 
              delta="Prejuízo" if lucro_operacional < 0 else "Lucro", 
              delta_color="normal" if lucro_operacional > 0 else "inverse")

    st.markdown("---")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ponto de Equilíbrio", f"{int(pe_qtd)} cortes")
    k2.metric("VPL (Riqueza)", f"R$ {vpl:,.2f}")
    k3.metric("Payback", f"{payback_mes} meses" if payback_mes else "Nunca")
    cor_ms = "normal" if margem_seguranca > 20 else ("off" if margem_seguranca > 0 else "inverse")
    k4.metric("Margem de Segurança", f"{margem_seguranca:.1f}%", delta_color=cor_ms)

    tab1, tab2 = st.tabs(["📈 Curva Financeira", "🤖 O Consultor Sincero"])
    
    with tab1:
        st.line_chart(df_grafico, x="Mês", y="Saldo Acumulado")
    
    with tab2:
        st.subheader("Análise Detalhada de Viabilidade")
        
        # --- AVALIAÇÃO DETALHADA RESTAURADA ---
        
        # 1. ANÁLISE OPERACIONAL (Dia a dia)
        st.markdown("#### 1. Diagnóstico Operacional")
        if lucro_operacional < 0:
            st.error(f"❌ **PREJUÍZO MENSAL:** A sua barbearia perde R$ {abs(lucro_operacional):.2f} todos os meses. Antes de pensar no investimento, você precisa resolver o dia a dia. Aumente o preço, reduza custos ou venda mais.")
        elif margem_seguranca < 10:
            st.warning(f"⚠️ **OPERAÇÃO DE RISCO:** Você tem lucro, mas sua Margem de Segurança é baixa ({margem_seguranca:.1f}%). Qualquer queda pequena nas vendas te coloca no prejuízo.")
        else:
            st.success(f"✅ **OPERAÇÃO SAUDÁVEL:** O negócio gera caixa mensalmente com uma margem de segurança de {margem_seguranca:.1f}%.")

        st.markdown("---")
        
        # 2. ANÁLISE DO INVESTIMENTO (Futuro)
        st.markdown("#### 2. Viabilidade do Investimento")
        
        if lucro_operacional > 0:
            # Caso A: Lucro Operacional existe, mas VPL é negativo
            if vpl < 0:
                st.warning(f"""
                **VEREDITO: CUIDADO (Destruição de Valor)**
                
                Embora a barbearia dê lucro mensal, **o investimento NÃO compensa financeiramente** comparado a deixar o dinheiro aplicado.
                
                * **O Problema:** O seu dinheiro renderia mais se ficasse parado no banco ganhando {tma_anual}% ao ano.
                * **O VPL é Negativo:** Você está "perdendo" R$ {abs(vpl):.2f} em valor presente ao escolher abrir este negócio em vez de investir no mercado financeiro.
                * **Sugestão:** Para valer a pena, você precisa aumentar o lucro mensal para que o Payback seja mais rápido.
                """)
            
            # Caso B: Lucro Operacional existe e VPL é positivo
            else:
                st.success(f"""
                **VEREDITO: APROVADO (Geração de Riqueza)**
                
                Excelente oportunidade! O projeto paga o investimento e ainda gera lucro real acima da inflação/juros.
                
                * **Criação de Valor:** O projeto coloca R$ {vpl:.2f} de riqueza líquida no seu bolso (trazidos a valor de hoje).
                * **Eficiência:** Para cada R$ 1,00 investido, você recebe de volta R$ {indice_lucratividade:.2f}.
                * **Rentabilidade Real (TIR):** Seu dinheiro rende **{tir_anual*100:.1f}% ao ano** aqui. Muito mais que os {tma_anual}% do banco.
                """)
        else:
            st.error("**VEREDITO: REPROVADO.** Não invista enquanto a operação estiver dando prejuízo mensal.")

if __name__ == "__main__":
    main()
