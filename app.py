import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

import goldsense_core as core

BKK = ZoneInfo("Asia/Bangkok")

st.set_page_config(
    page_title="GoldSense",
    page_icon="🪙",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Mobile-first styling (navy + gold)
st.markdown("""
<style>
.block-container{max-width:760px;padding-top:2.2rem;padding-bottom:4rem}
h1,h2,h3{color:#f2cf86!important}
[data-testid="stMetric"]{background:#172238;border:1px solid #344563;
  padding:14px 16px;border-radius:16px}
[data-testid="stMetricLabel"] p{font-size:.85rem;color:#acbad1}
.stButton>button{width:100%;border-radius:12px;min-height:46px;font-weight:600}
#MainMenu, footer{visibility:hidden}
@media (max-width:640px){
  .block-container{padding:1.2rem .8rem 4rem}
  h1{font-size:1.7rem!important}
  [data-testid="stMetricValue"]{font-size:1.5rem}
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)
def load_prices():
    return core.load_prices()


@st.cache_data(show_spinner=False)
def analyze(prices):
    return core.analyze(prices)


def bkk_time(iso):
    return dt.datetime.fromisoformat(iso).astimezone(BKK).strftime("%d/%m/%Y %H:%M")


st.title("🪙 GoldSense")
st.caption("ต้นแบบวิจัยทองล่วงหน้า (GC=F) · ไม่ใช่ราคาทองไทย · ไม่ใช่คำแนะนำลงทุน")

if st.button("🔄 ตรวจข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()


@st.fragment(run_every="1h")
def dashboard():
    try:
        with st.spinner("กำลังโหลดราคาและคำนวณโมเดล..."):
            prices, fetched = load_prices()
            p, expected, scores, impacts = analyze(prices)
    except Exception as error:
        st.error(f"ยังไม่สามารถวิเคราะห์: {error}")
        st.info("ลองกด 'ตรวจข้อมูลใหม่' อีกครั้งในอีกสักครู่")
        return

    stale = core.data_age_days(prices) > core.STALE_DAYS
    st.caption(
        f"ข้อมูลถึง {prices.index[-1]:%d/%m/%Y} · "
        f"ตรวจล่าสุด {bkk_time(fetched)} (เวลาไทย) · อัปเดตทุกชั่วโมงขณะเปิดแอป"
    )
    if stale:
        st.error(f"ข้อมูลเก่ากว่า {core.STALE_DAYS} วัน ระงับการแสดงคาดการณ์")

    st.metric("ราคาปิดอ้างอิง (USD/oz)", f"{prices.gold.iloc[-1]:,.2f}")
    a, b = st.columns(2)
    a.metric("โอกาสขึ้น", "—" if stale else f"{p:.1%}")
    b.metric("ผลตอบแทนที่คาด", "—" if stale else f"{expected:+.2%}")

    overview, audit, notes = st.tabs(["ภาพรวม", "ตรวจสอบ", "ข้อจำกัด"])
    with overview:
        fig = px.line(
            prices.tail(120), y="gold",
            template="plotly_dark", color_discrete_sequence=["#f2cf86"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="", yaxis_title="USD/oz", showlegend=False,
            height=300, margin=dict(l=0, r=0, t=10, b=0), dragmode=False,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        if not stale:
            st.subheader("บทวิเคราะห์จากข้อมูล")
            st.write(core.commentary(prices, p, expected))

    with audit:
        labels = {
            "accuracy": "Accuracy โมเดล",
            "always_up": "Accuracy ถ้าทายขึ้นทุกวัน",
            "brier": "Brier โมเดล",
            "baseline_brier": "Brier ค่าฐาน",
            "mae": "MAE โมเดล",
            "zero_return_mae": "MAE ถ้าทายศูนย์",
            "samples": "จำนวนตัวอย่างทดสอบ",
        }
        table = pd.DataFrame({
            "ตัวชี้วัด": [labels[k] for k in scores],
            "ค่า": [f"{v:,}" if k == "samples" else f"{v:.4f}" for k, v in scores.items()],
        })
        st.dataframe(table, hide_index=True, width="stretch")
        st.caption(
            "Accuracy สูงกว่าดีกว่า; Brier และ MAE ต่ำกว่าดีกว่า "
            "(MAE 0.01 = 1 จุดเปอร์เซ็นต์)"
        )
        st.dataframe(
            impacts.round(4), hide_index=True, width="stretch",
            column_config={"factor": "ปัจจัย", "log_odds_contribution": "log-odds"},
        )
        st.caption("Contribution เป็นคะแนน log-odds ไม่ใช่ผลกระทบต่อราคา และไม่ใช่เหตุและผล")

    with notes:
        st.write(
            "แบ่งข้อมูลตามเวลา 80/20 เว้นหนึ่งแถวก่อนทดสอบ "
            "หน่วงปัจจัยหนึ่งแถว ไม่เติมข้อมูลด้วยค่าในอนาคต "
            "ยังเป็น holdout ครั้งเดียว ไม่ใช่ walk-forward "
            "ต้องเพิ่ม calibration ปฏิทินตลาด ข่าว และฐานข้อมูล "
            "อนุกรมทองล่วงหน้าอาจมีผลจากการเปลี่ยนสัญญา"
        )


dashboard()
