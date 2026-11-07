import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Configurazione della pagina Streamlit (ottimizzata per Mobile/iPhone)
st.set_page_config(
    page_title="Verifica Fuori Piano NTC 2018",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏗️ Verifica Fuori Piano NTC 2018")
st.caption("Verifica a pressoflessione fuori piano di setti murari secondo NTC 2018 e Circolare 7/2019")

# --- SIDEBAR: INPUT DEI DATI ---
st.sidebar.header("1. Geometria e Materiali")
h = st.sidebar.number_input("Altezza setto h (m)", value=3.50, step=0.10)
t = st.sidebar.number_input("Spessore setto t (m)", value=0.50, step=0.05)
b = st.sidebar.number_input("Larghezza di calcolo b (m)", value=1.00, step=0.10)
gamma = st.sidebar.number_input("Peso spec. muratura γ (kN/m³)", value=19.00, step=0.50)
N_d = st.sidebar.number_input("Carico assiale in testa N_d (kN/m)", value=60.00, step=5.00)
f_m = st.sidebar.number_input("Resistenza mef. compr. f_m (N/mm²)", value=1.80, step=0.10)
FC = st.sidebar.number_input("Fattore Confidenza FC", value=1.35, step=0.05)
gamma_M = st.sidebar.number_input("Coeff. parziale materiale γ_M", value=2.00, step=0.10)
schema = st.sidebar.selectbox("Schema Vincolare", ["Appoggiato", "Semi-incastro", "Mensola"])

st.sidebar.header("2. Sismica di Sito (NTC 2018)")
a_g = st.sidebar.number_input("Accelerazione di picco a_g (g)", value=0.215, step=0.005, format="%.3f")
F_0 = st.sidebar.number_input("Fattore spettrale F_0", value=2.45, step=0.05)
cat_suolo = st.sidebar.selectbox("Categoria Sottosuolo", ["A", "B", "C", "D", "E"], index=1)
S_T = st.sidebar.number_input("Coeff. Topografico S_T", value=1.00, step=0.05)
z = st.sidebar.number_input("Quota baricentro setto z (m)", value=3.50, step=0.50)
H_edificio = st.sidebar.number_input("Altezza totale edificio H (m)", value=10.50, step=0.50)
q_a = st.sidebar.number_input("Fattore di struttura q_a", value=2.00, step=0.10)

# --- MOTORE DI CALCOLO NTC 2018 ---
ag_F0 = a_g * F_0
if cat_suolo == "A":
    S_S = 1.00
elif cat_suolo == "B":
    S_S = max(1.00, min(1.20, 1.40 - 0.40 * ag_F0))
elif cat_suolo == "C":
    S_S = max(1.00, min(1.50, 1.70 - 0.60 * ag_F0))
elif cat_suolo == "D":
    S_S = max(0.90, min(1.80, 2.40 - 1.50 * ag_F0))
elif cat_suolo == "E":
    S_S = max(1.00, min(1.60, 2.00 - 1.10 * ag_F0))
else:
    S_S = 1.20

def calcola_verifiche(h_val):
    S = S_S * S_T
    a_max = a_g * S
    T_1 = 0.05 * (H_edificio ** 0.75)
    T_a = 0.05 * (h_val ** 0.75)
    psi_z = min(3.0, 1.0 + 2.0 * (z / H_edificio))
    A_n = 3.0 / (1.0 + ((1.0 - (T_a / T_1)) ** 2)) if T_1 > 0 else 1.0
    S_a = a_max * psi_z * A_n
    C_a = S_a / q_a

    f_d = (f_m / (FC * gamma_M)) * 1000.0 # kN/m²
    P_parete = gamma * t * h_val * b
    N_med = N_d + P_parete / 2.0
    N_base = N_d + P_parete
    q_s = C_a * (gamma * t * b)

    if schema == "Mensola":
        M_d_sisma = (q_s * (h_val ** 2)) / 2.0
        e_a = h_val / 300.0
        M_d_ecc = N_base * e_a
        N_calc = N_base
    elif schema == "Semi-incastro":
        M_d_sisma = (q_s * (h_val ** 2)) / 12.0
        e_a = h_val / 300.0
        M_d_ecc = N_med * e_a
        N_calc = N_med
    else: # Appoggiato
        M_d_sisma = (q_s * (h_val ** 2)) / 8.0
        e_a = h_val / 300.0
        M_d_ecc = N_med * e_a
        N_calc = N_med

    M_Ed = M_d_sisma + M_d_ecc
    u = N_calc / (b * f_d)
    z_braccio = (t / 2.0) - (u / 2.0)
    M_Rd_0 = N_calc * z_braccio
    e_tot = M_Ed / N_calc if N_calc > 0 else 0.0
    phi = max(0.0, 1.0 - 2.0 * (e_tot / t))
    M_Rd = phi * M_Rd_0

    return C_a, N_calc, M_Ed, M_Rd

# Calcolo per l'altezza inserita
C_a, N_calc, M_Ed, M_Rd = calcola_verifiche(h)
dc_ratio = (M_Ed / M_Rd) if M_Rd > 0 else 999.99

# --- DISPLAY RISULTATI ---
col1, col2, col3 = st.columns(3)
col1.metric("Coeff. Sismico C_a", f"{C_a:.4f}")
col2.metric("Momento Agente M_Ed", f"{M_Ed:.2f} kNm")
col3.metric("Momento Resistente M_Rd", f"{M_Rd:.2f} kNm")

st.markdown("---")

if M_Rd <= 0 or dc_ratio > 1.0:
    st.error(f"❌ **NON VERIFICATO** — Rapporto di Sfruttamento D/C = **{dc_ratio:.3f}**")
else:
    st.success(f"✔ **VERIFICATO** — Rapporto di Sfruttamento D/C = **{dc_ratio:.3f}**")

# --- GRAFICI INTERATTIVI ---
tab1, tab2 = st.tabs(["📊 Confronto Diretto", "📈 Curva di Sensibilità h"])

with tab1:
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    bars = ax1.bar(["M_Ed (Agente)", "M_Rd (Resistente)"], [M_Ed, M_Rd], color=["#C65911", "#1F4E78"])
    ax1.set_ylabel("Momento (kNm)")
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, height + 0.2, f"{height:.2f} kNm", ha='center', va='bottom', fontweight='bold')
    st.pyplot(fig1)

with tab2:
    h_range = np.linspace(2.0, 6.0, 50)
    m_ed_list = [calcola_verifiche(hi)[2] for hi in h_range]
    m_rd_list = [calcola_verifiche(hi)[3] for hi in h_range]

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.plot(h_range, m_ed_list, label="M_Ed Agente", color="#C65911", linewidth=2.5)
    ax2.plot(h_range, m_rd_list, label="M_Rd Resistente", color="#1F4E78", linewidth=2.5)
    ax2.axvline(x=h, color="gray", linestyle=":", label=f"h attuale ({h:.2f}m)")
    ax2.set_xlabel("Altezza Setto h (m)")
    ax2.set_ylabel("Momento (kNm)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.7)
    st.pyplot(fig2)