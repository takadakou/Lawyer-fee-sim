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
    # パスワードはここで自由に変更してください
    if st.session_state["password"] == "office2024":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 2. 認証チェックの実行 ---
if check_password():

    # --- 3. 共通計算ロジック ---
    def calculate_fee(amount, brackets):
        total_fee = 0
        for lower, upper, rate in brackets:
            if amount > lower:
                target = min(amount, upper) - lower
                total_fee += target * (rate / 100)
        return total_fee

    # --- 4. UI初期設定 ---
    st.set_page_config(page_title="報酬シミュレーター Switch版", layout="wide")
    st.title("⚖️ 弁護士報酬シミュレーター")

    # --- 5. サイドバー：共通設定 ---
    st.sidebar.header("📊 基本データ設定")
    
    # モード切り替えスイッチ
    app_mode = st.sidebar.radio(
        "モード選択",
        ["① 現行基準を確認", "② 改定案をシミュレーション"]
    )
    
    # 顧客分布（案件数）のエディタ
    st.sidebar.write("---")
    st.sidebar.subheader("案件分布（自由に編集可）")
    base_data = pd.DataFrame({
        "解決金 (円)": [500000, 1500000, 5000000, 10000000, 50000000, 400000000],
        "案件数": [100, 10, 8, 5, 2, 1]
    })
    edited_df = st.sidebar.data_editor(base_data, num_rows="dynamic")

    # --- 6. 報酬ロジックの定義（スイッチによる分岐） ---

    # 現行基準（ Old Logic: 固定またはデフォルト値 ）
    current_brackets = [
        (0, 3_000_000, 20.0),
        (3_000_000, 30_000_000, 15.0),
        (30_000_000, 300_000_000, 10.0),
        (300_000_000, float('inf'), 6.0)
    ]

    # 改定案の初期化（シミュレーション用）
    if app_mode == "② 改定案をシミュレーション":
        st.subheader("🛠 改定案のパラメータ調整")
        st.info("スライダーや入力ボックスで、新しい報酬体系を自由に構築してください。")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.write("**【境界金額 (万円)】**")
            b1 = st.number_input("第1境界", 100, 1000, 300, 10) * 10000
            b2 = st.number_input("第2境界", 1000, 5000, 3000, 50) * 10000
            b3 = st.number_input("第3境界", 5000, 50000, 30000, 500) * 10000
        with col_p2:
            st.write("**【報酬割合 (%)】**")
            r1 = st.number_input("新 第1層", 0.0, 40.0, 20.0, 0.1)
            r2 = st.number_input("新 第2層", 0.0, 40.0, 15.0, 0.1)
            r3 = st.number_input("新 第3層", 0.0, 40.0, 10.0, 0.1)
            r4 = st.number_input("新 第4層", 0.0, 40.0, 6.0, 0.1)
        with col_p3:
            st.write("**【市場反応】**")
            retention = st.slider("想定維持率 (%)", 50.0, 100.0, 95.0, 0.5) / 100
            st.caption(f"維持率: {retention*100:.1f}%")

        new_brackets = [(0, b1, r1), (b1, b2, r2), (b2, b3, r3), (b3, float('inf'), r4)]
    else:
        # 現行モードのときは、改定案も現行と同じにしておく（比較のため）
        st.subheader("✅ 現在の報酬体系を表示中")
        st.success("サイドバーで『シミュレーションモード』に切り替えると数値を変更できます。")
        new_brackets = current_brackets
        retention = 1.0

    # --- 7. 計算実行と可視化 ---

    # 報酬総額の算出
    current_rev = sum(calculate_fee(r[0], current_brackets) * r[1] for r in edited_df.values)
    new_rev_100 = sum(calculate_fee(r[0], new_brackets) * r[1] for r in edited_df.values)
    new_rev_actual = new_rev_100 * retention

    st.divider()
    
    # サマリー表示
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("現状の総報酬", f"{int(current_rev):,}円")
    with m_col2:
        diff = new_rev_actual - current_rev
        delta_label = f"{(diff/current_rev*100):+.1f}%" if current_rev > 0 else "0%"
        st.metric("改定後の想定総報酬", f"{int(new_rev_actual):,}円", delta=f"{int(diff):+,}円 ({delta_label})")
    with m_col3:
        be_ret = (current_rev / new_rev_100) if new_rev_100 > 0 else 0
        st.metric("損益分岐となる維持率", f"{be_ret*100:.1f}%")

    # 収益比較グラフ
    chart_data = pd.DataFrame({
        "プラン": ["現状", "改定案(100%維持)", "改定案(想定維持率)"],
        "報酬額": [current_rev, new_rev_100, new_rev_actual]
    })
    st.bar_chart(chart_data, x="プラン", y="報酬総額")

    # --- 8. 詳細比較テーブル & CSV ---
    st.divider()
    st.subheader("🧐 1件あたりの詳細比較")
    
    sample_amounts = [500_000, 1_500_000, 3_000_000, 5_000_000, 10_000_000, 30_000_000, 100_000_000, 500_000_000]
    comparison_df = pd.DataFrame([{
        "解決金額": f"{amt:,}円",
        "現状報酬": int(calculate_fee(amt, current_brackets)),
        "新案報酬": int(calculate_fee(amt, new_brackets)),
        "差額": int(calculate_fee(amt, new_brackets) - calculate_fee(amt, current_brackets))
    } for amt in sample_amounts])
    
    st.table(comparison_df)

    csv = comparison_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📊 比較表をCSVで保存", data=csv, file_name='fee_sim_result.csv', mime='text/csv')
