import streamlit as st
import pandas as pd

# --- 計算ロジック ---
def calculate_fee(settlement_amount, fee_brackets):
    total_fee = 0
    for lower, upper, rate in fee_brackets:
        if settlement_amount > lower:
            target = min(settlement_amount, upper) - lower
            total_fee += target * (rate / 100)
    return total_fee

# --- UIの設定 ---
st.set_page_config(page_title="弁護士報酬シミュレーター Pro", layout="wide")
st.title("⚖️ 弁護士報酬改定シミュレーター")

# --- サイドバー：1. 顧客分布データ ---
st.sidebar.header("1. 顧客分布データ")
base_data = pd.DataFrame({
    "解決金 (円)": [500000, 1500000, 5000000, 10000000, 50000000, 400000000],
    "案件数": [100, 10, 8, 5, 2, 1]
})
edited_df = st.sidebar.data_editor(base_data, num_rows="dynamic")

# --- サイドバー：2. 現状の基準 (ここを修正しました) ---
st.sidebar.header("2. 現状の報酬基準 (%)")
st.sidebar.info("比較のベースとなる現在の基準を入力してください。")
c_r1 = st.sidebar.number_input("現状: 第1層 (%)", value=20.0, step=0.5)
c_r2 = st.sidebar.number_input("現状: 第2層 (%)", value=15.0, step=0.5)
c_r3 = st.sidebar.number_input("現状: 第3層 (%)", value=10.0, step=0.5)
c_r4 = st.sidebar.number_input("現状: 第4層 (%)", value=6.0, step=0.5)

current_brackets = [
    (0, 3_000_000, c_r1),
    (3_000_000, 30_000_000, c_r2),
    (30_000_000, 300_000_000, c_r3),
    (300_000_000, float('inf'), c_r4)
]

# --- メイン画面：改定案の作成 ---
st.subheader("📝 改定案のシミュレーション")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.write("**【境界金額の変更 (万円)】**")
    b1 = st.slider("第1境界 (初期300万)", 100, 1000, 300, step=50) * 10000
    b2 = st.slider("第2境界 (初期3000万)", 1000, 5000, 3000, step=100) * 10000
    b3 = st.slider("第3境界 (初期3億)", 5000, 50000, 30000, step=1000) * 10000

with col_p2:
    st.write("**【改定案の割合 (%)】**")
    r1 = st.slider("新 第1層", 0.0, 40.0, 20.0, 0.5)
    r2 = st.slider("新 第2層", 0.0, 30.0, 15.0, 0.5)
    r3 = st.slider("新 第3層", 0.0, 20.0, 10.0, 0.5)
    r4 = st.slider("新 第4層", 0.0, 15.0, 6.0, 0.5)

with col_p3:
    st.write("**【市場の反応】**")
    retention = st.slider("想定される顧客維持率 (%)", 50, 100, 95) / 100
    st.write(f"維持率: {retention*100:.0f}% （顧客の {100-retention*100:.0f}% が離脱すると想定）")

# 改定案の組み立て
new_brackets = [
    (0, b1, r1),
    (b1, b2, r2),
    (b2, b3, r3),
    (b3, float('inf'), r4)
]

# --- 計算実行 ---
current_total = sum(calculate_fee(row[0], current_brackets) * row[1] for row in edited_df.values)
new_total_100 = sum(calculate_fee(row[0], new_brackets) * row[1] for row in edited_df.values)
new_total_actual = new_total_100 * retention

# --- 結果の表示 ---
st.divider()
res_col1, res_col2 = st.columns([2, 1])

with res_col1:
    st.subheader("📊 収益比較")
    # グラフ表示
    chart_data = pd.DataFrame({
        "プラン": ["現状", "改定案(100%維持)", "改定案(想定維持率)"],
        "報酬総額": [current_total, new_total_100, new_total_actual]
    })
    st.bar_chart(chart_data, x="プラン", y="報酬総額")

with res_col2:
    st.subheader("💰 収支サマリー")
    diff = new_total_actual - current_total
    percent = (diff / current_total * 100) if current_total > 0 else 0
    st.metric("改定後の想定報酬額", f"{int(new_total_actual):,} 円", delta=f"{int(diff):+,} 円 ({percent:+.1f}%)")
    
    be_retention = (current_total / new_total_100) if new_total_100 > 0 else 0
    st.info(f"💡 損益分岐点\n\n顧客が **{100 - be_retention*100:.1f}%** 減少するまで現状を維持できます。")

# --- 詳細テーブルの表示 ---
st.divider()
st.subheader("🧐 1件あたりの報酬額 比較表")
sample_amounts = [500_000, 1_000_000, 3_000_000, 5_000_000, 10_000_000, 30_000_000, 100_000_000]
comparison_rows = []
for amt in sample_amounts:
    c_f = calculate_fee(amt, current_brackets)
    n_f = calculate_fee(amt, new_brackets)
    comparison_rows.append({
        "解決金額": f"{amt:,}円",
        "現状の報酬": f"{int(c_f):,}円",
        "改定案の報酬": f"{int(n_f):,}円",
        "差額": f"{int(n_f - c_f):+,}円"
    })
st.table(pd.DataFrame(comparison_rows))