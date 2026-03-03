import streamlit as st
import pandas as pd

# --- 1. パスワード制限機能 ---
def check_password():
    """認証に成功したらTrue、失敗したらFalseを返す"""
    if "password_correct" not in st.session_state:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワードが違います。もう一度入力してください", type="password", on_change=password_entered, key="password")
        st.error("😕 パスワードが正しくありません")
        return False
    return True

def password_entered():
    """入力されたパスワードをチェックする"""
    # パスワードはここで自由に変更してください
    if st.session_state["password"] == "office2024":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 認証チェックの実行 ---
if check_password():

    # --- 2. 計算ロジック (超過累進計算) ---
    def calculate_fee(amount, brackets):
        total_fee = 0
        for lower, upper, rate in brackets:
            if amount > lower:
                # その層の枠に収まる金額を抽出
                target = min(amount, upper) - lower
                total_fee += target * (rate / 100)
        return total_fee

    # --- 3. UI初期設定 ---
    st.set_page_config(page_title="報酬シミュレーター Pro", layout="wide")
    st.title("⚖️ 弁護士報酬シミュレーター：現行 vs 改定案")

    # --- 4. サイドバー：1.案件分布 ＆ 2.現状の基準 ---
    st.sidebar.header("📊 1. 案件分布（ベースデータ）")
    
    # 初期データ
    base_data = pd.DataFrame({
        "解決金 (円)": [500000, 1500000, 5000000, 10000000, 50000000, 400000000],
        "案件数": [100, 10, 8, 5, 2, 1]
    })

    # データエディタ（カンマ区切り設定）
    edited_df = st.sidebar.data_editor(
        base_data, 
        num_rows="dynamic",
        column_config={
            "解決金 (円)": st.column_config.NumberColumn(
                "解決金 (円)",
                format="%d", # 3桁区切りのカンマを表示
                min_value=0,
            ),
            "案件数": st.column_config.NumberColumn(
                "案件数",
                min_value=0,
                step=1
            )
        }
    )

    st.sidebar.divider()
    st.sidebar.header("📉 2. 現状の基準設定")
    st.sidebar.caption("比較元となる現在の基準を入力してください。")
    
    # 現状の境界金額（左側の入力欄）
    cb1 = st.sidebar.number_input("現状: 第1境界", 100, 1000, 300, 10, key="cb1") * 10000
    cb2 = st.sidebar.number_input("現状: 第2境界", 1000, 5000, 3000, 50, key="cb2") * 10000
    cb3 = st.sidebar.number_input("現状: 第3境界", 5000, 50000, 30000, 500, key="cb3") * 10000
    
    # 現状の割合（左側のスライダー）
    cr1 = st.sidebar.slider("現状: 第1層 (%)", 0.0, 40.0, 20.0, 0.5, key="cr1")
    cr2 = st.sidebar.slider("現状: 第2層 (%)", 0.0, 40.0, 15.0, 0.5, key="cr2")
    cr3 = st.sidebar.slider("現状: 第3層 (%)", 0.0, 40.0, 10.0, 0.5, key="cr3")
    cr4 = st.sidebar.slider("現状: 第4層 (%)", 0.0, 40.0, 6.0, 0.5, key="cr4")

    current_brackets = [
        (0, cb1, cr1),
        (cb1, cb2, cr2),
        (cb2, cb3, cr3),
        (cb3, float('inf'), cr4)
    ]

    # --- 5. メイン画面：3.改定案の設定 ---
    st.subheader("🛠 3. 改定案のパラメータ調整")
    st.info("💡 数値入力ボックスは、横の＋/－ボタンやキーボード入力で微調整が可能です。")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.write("**【境界金額 (万円)】**")
        nb1 = st.number_input("改定: 第1境界", 100, 1000, 300, 10) * 10000
        nb2 = st.number_input("改定: 第2境界", 1000, 5000, 3000, 50) * 10000
        nb3 = st.number_input("改定: 第3境界", 5000, 50000, 30000, 500) * 10000
    with col_p2:
        st.write("**【報酬割合 (%)】**")
        nr1 = st.number_input("改定: 第1層", 0.0, 40.0, 22.0, 0.1, format="%.1f")
        nr2 = st.number_input("改定: 第2層", 0.0, 40.0, 17.0, 0.1, format="%.1f")
        nr3 = st.number_input("改定: 第3層", 0.0, 40.0, 11.0, 0.1, format="%.1f")
        nr4 = st.number_input("改定: 第4層", 0.0, 40.0, 7.0, 0.1, format="%.1f")
    with col_p3:
        st.write("**【市場反応】**")
        retention = st.slider("想定される顧客維持率 (%)", 50.0, 100.0, 95.0, 0.5) / 100
        st.write(f"維持率: {retention*100:.1f}% （顧客の {100-retention*100:.1f}% が離脱すると想定）")

    new_brackets = [(0, nb1, nr1), (nb1, nb2, nr2), (nb2, nb3, nr3), (nb3, float('inf'), nr4)]

    # --- 6. 計算実行と分析 ---
    current_total = sum(calculate_fee(r[0], current_brackets) * r[1] for r in edited_df.values)
    new_total_100 = sum(calculate_fee(r[0], new_brackets) * r[1] for r in edited_df.values)
    new_total_actual = new_total_100 * retention

    st.divider()
    
    # メトリクス（数値）表示
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("現状の総報酬額", f"{int(current_total):,}円")
    with m_col2:
        diff = new_total_actual - current_total
        delta_label = f"{(diff/current_total*100):+.1f}%" if current_total > 0 else "0%"
        st.metric("改定後の想定総報酬", f"{int(new_total_actual):,}円", delta=f"{int(diff):+,}円 ({delta_label})")
    with m_col3:
        # 損益分岐点の計算
        be_ret = (current_total / new_total_100) if new_total_100 > 0 else 0
        st.metric("損益分岐となる維持率", f"{be_ret*100:.1f}%")
        st.caption(f"顧客が {100 - be_ret*100:.1f}% 以上減ると減収になります。")

    # 収益比較グラフ
    chart_data = pd.DataFrame({
        "プラン": ["現状", "改定案(100%維持)", "改定案(想定維持率)"],
        "報酬総額": [current_total, new_total_100, new_total_actual]
    })
    st.bar_chart(chart_data, x="プラン", y="報酬総額")

    # --- 7. 詳細テーブル ＆ CSV ---
    st.divider()
    st.subheader("🧐 1件あたりの詳細比較表")
    
    sample_amounts = [500_000, 1_500_000, 3_000_000, 5_000_000, 10_000_000, 30_000_000, 100_000_000, 500_000_000]
    comparison_rows = []
    for amt in sample_amounts:
        c_f = calculate_fee(amt, current_brackets)
        n_f = calculate_fee(amt, new_brackets)
        comparison_rows.append({
            "解決金額": amt,
            "現状報酬": int(c_f),
            "改定報酬": int(n_f),
            "1件あたりの差額": int(n_f - c_f)
        })
    
    comparison_df = pd.DataFrame(comparison_rows)
    
    # 画面表示用のフォーマット済みテーブル
    st.table(comparison_df.style.format("{:,}"))

    # CSVダウンロード機能
    csv = comparison_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📊 比較データをCSVとしてダウンロード",
        data=csv,
        file_name='lawyer_fee_comparison_report.csv',
        mime='text/csv',
    )
