import streamlit as st
import pandas as pd

# --- 1. パスワード制限機能 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワードが違います", type="password", on_change=password_entered, key="password")
        st.error("😕 パスワードが正しくありません")
        return False
    return True

def password_entered():
    if st.session_state["password"] == "Tokyo":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 認証チェックの実行 ---
if check_password():

    # --- 2. 計算ロジック ---
    def calculate_fee(amount, brackets):
        total_fee = 0
        for lower, upper, rate in brackets:
            if amount > lower:
                target = min(amount, upper) - lower
                total_fee += target * (rate / 100)
        return total_fee

    # --- 3. UI初期設定 ---
    st.set_page_config(page_title="報酬シミュレーター Pro", layout="wide")
    st.title("⚖️ 弁護士報酬シミュレーター")

    # --- 4. サイドバー：案件分布 ＆ 現状の基準 ---
    st.sidebar.header("1. 案件分布（ベースデータ）")
    
    # ユーザーが手直しした初期データ
    base_data = pd.DataFrame({
        "解決金 (円)": [500000, 1000000, 1500000, 3000000, 5000000, 10000000, 30000000, 100000000, 200000000],
        "案件数": [200, 150, 80, 50, 30, 18, 10, 10, 4]
    })

    # 解決金にカンマを表示
    edited_df = st.sidebar.data_editor(
        base_data, 
        num_rows="dynamic",
        column_config={
            "解決金 (円)": st.column_config.NumberColumn(
                "解決金 (円)",
                format="%d", 
                min_value=0,
            ),
            "案件数": st.column_config.NumberColumn(
                "案件数",
                format="%d",
                min_value=0,
                step=1
            )
        }
    )

    st.sidebar.divider()
    st.sidebar.header("2. 現状の基準設定")
    
    cb1 = st.sidebar.number_input("現状: 第1境界 (万円)", 100, 1000, 300, 10, key="cb1") * 10000
    cb2 = st.sidebar.number_input("現状: 第2境界 (万円)", 1000, 5000, 3000, 50, key="cb2") * 10000
    cb3 = st.sidebar.number_input("現状: 第3境界 (万円)", 5000, 50000, 30000, 500, key="cb3") * 10000
    
    cr1 = st.sidebar.number_input("現状: 第1層 (%)", 0.0, 40.0, 24.0, 0.5, key="cr1")
    cr2 = st.sidebar.number_input("現状: 第2層 (%)", 0.0, 40.0, 15.0, 0.5, key="cr2")
    cr3 = st.sidebar.number_input("現状: 第3層 (%)", 0.0, 40.0, 9.0, 0.5, key="cr3")
    cr4 = st.sidebar.number_input("現状: 第4層 (%)", 0.0, 40.0, 4.5, 0.5, key="cr4")

    current_brackets = [(0, cb1, cr1), (cb1, cb2, cr2), (cb2, cb3, cr3), (cb3, float('inf'), cr4)]

    # --- 5. メイン画面：改定案の設定 ---
    st.subheader("3. 改定案のパラメータ調整")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.write("**【境界金額 (万円)】**")
        nb1 = st.number_input("改定: 第1境界 (万円)", 100, 1000, 500, 10) * 10000
        nb2 = st.number_input("改定: 第2境界 (万円)", 1000, 10000, 5000, 50) * 10000
        nb3 = st.number_input("改定: 第3境界 (万円)", 5000, 100000, 50000, 500) * 10000
    with col_p2:
        st.write("**【報酬割合 (%)】**")
        nr1 = st.number_input("改定: 第1層 (%)", 0.0, 40.0, 24.0, 0.1, format="%.1f")
        nr2 = st.number_input("改定: 第2層 (%)", 0.0, 40.0, 15.0, 0.1, format="%.1f")
        nr3 = st.number_input("改定: 第3層 (%)", 0.0, 40.0, 9.0, 0.1, format="%.1f")
        nr4 = st.number_input("改定: 第4層 (%)", 0.0, 40.0, 4.5, 0.1, format="%.1f")
    with col_p3:
        st.write("**【市場反応】**")
        retention_val = st.number_input("想定される顧客維持率 (%)", 50.0, 100.0, 95.0, 0.5)
        retention = retention_val / 100
        st.write(f"維持率: {retention*100:.1f}%")

    new_brackets = [(0, nb1, nr1), (nb1, nb2, nr2), (nb2, nb3, nr3), (nb3, float('inf'), nr4)]

    # --- 6. 計算とグラフ表示 ---
    current_total = sum(calculate_fee(r[0], current_brackets) * r[1] for r in edited_df.values)
    new_total_100 = sum(calculate_fee(r[0], new_brackets) * r[1] for r in edited_df.values)
    new_total_actual = new_total_100 * retention

    st.divider()
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("現状の総報酬額", f"{int(current_total):,}円")
    with m_col2:
        diff = new_total_actual - current_total
        delta_label = f"{(diff/current_total*100):+.1f}%" if current_total > 0 else "0%"
        st.metric("改定後の想定総報酬", f"{int(new_total_actual):,}円", delta=f"{int(diff):+,}円 ({delta_label})")
    with m_col3:
        be_ret = (current_total / new_total_100) if new_total_100 > 0 else 0
        st.metric("損益分岐となる維持率", f"{be_ret*100:.1f}%")

    # グラフ
    chart_data = pd.DataFrame({
        "プラン": ["現状", "改定案(100%維持)", "改定案(想定維持率)"],
        "報酬総額": [current_total, new_total_100, new_total_actual]
    })
    st.bar_chart(chart_data, x="プラン", y="報酬総額")

    # --- 7. 詳細テーブル ＆ CSV (案件分布データと連動) ---
    st.divider()
    st.subheader("🧐 案件分布に基づいた1件あたりの詳細比較表")
    
    # 案件分布（ベースデータ）から「解決金」のリストを取得
    # 重複を排除して、金額の小さい順に並べ替えます
    target_amounts = sorted(edited_df["解決金 (円)"].unique().tolist())
    
    comp_rows = []
    for amt in target_amounts:
        c_f = calculate_fee(amt, current_brackets)
        n_f = calculate_fee(amt, new_brackets)
        comp_rows.append({
            "解決金額": amt, 
            "現状報酬": int(c_f), 
            "改定報酬": int(n_f), 
            "差額": int(n_f - c_f)
        })
    
    comp_df = pd.DataFrame(comp_rows)
    st.table(comp_df.style.format("{:,}"))

    csv = comp_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📊 比較データをCSVで保存", data=csv, file_name='fee_comparison_report.csv', mime='text/csv')
