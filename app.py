import streamlit as st
import pandas as pd

# --- 1. パスワード制限機能 ---
def check_password():
    """認証に成功したらTrue、失敗したらFalseを返す"""
    if "password_correct" not in st.session_state:
        # 初期状態：パスワード入力画面を表示
        st.text_input(
            "パスワードを入力してください", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # 失敗時：再入力を促す
        st.text_input(
            "パスワードが違います。もう一度入力してください", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 パスワードが正しくありません")
        return False
    else:
        # 認証済み
        return True

def password_entered():
    """入力されたパスワードをチェックする"""
    # ここに好きなパスワードを設定してください（例: "office2024"）
    if st.session_state["password"] == "Tokyo":
        st.session_state["password_correct"] = True
        del st.session_state["password"]  # セキュリティのため入力を消去
    else:
        st.session_state["password_correct"] = False

# --- 認証チェックの実行 ---
if check_password():

    # --- 2. 計算ロジック ---
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

    # --- サイドバー：設定 ---
    st.sidebar.header("1. 顧客分布データ")
    base_data = pd.DataFrame({
        "解決金 (円)": [500000, 1500000, 5000000, 10000000, 50000000, 400000000],
        "案件数": [100, 10, 8, 5, 2, 1]
    })
    edited_df = st.sidebar.data_editor(base_data, num_rows="dynamic")

    st.sidebar.header("2. 現状の報酬基準 (%)")
    c_r1 = st.sidebar.number_input("現状: 第1層 (%)", value=20.0, step=0.5)
    c_r2 = st.sidebar.number_input("現状: 第2層 (%)", value=15.0, step=0.5)
    c_r3 = st.sidebar.number_input("現状: 第3層 (%)", value=10.0, step=0.5)
    c_r4 = st.sidebar.number_input("現状: 第4層 (%)", value=6.0, step=0.5)

    current_brackets = [(0, 3e6, c_r1), (3e6, 3e7, c_r2), (3e7, 3e8, c_r3), (3e8, float('inf'), c_r4)]


    # --- メイン画面：改定案の作成 (操作性改善版) ---
    st.subheader("📝 改定案の詳細設定")
    st.info("💡 スライダーで大まかに動かし、右側の入力ボックスで微調整が可能です。")
    
    # 境界金額の設定（スライダーの刻みを細かくし、入力欄も追加）
    st.write("**【境界金額の変更 (万円)】**")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        b1 = st.number_input("第1境界", min_value=100, max_value=1000, value=300, step=10) * 10000
    with col_b2:
        b2 = st.number_input("第2境界", min_value=1000, max_value=5000, value=3000, step=50) * 10000
    with col_b3:
        b3 = st.number_input("第3境界", min_value=5000, max_value=50000, value=30000, step=500) * 10000
    
    # 報酬割合の設定（スライダーと数値入力を併用）
    st.write("**【各層の報酬割合 (%)】**")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    
    with col_r1:
        r1 = st.number_input("新 第1層 (%)", 0.0, 40.0, 20.0, step=0.1, format="%.1f")
    with col_r2:
        r2 = st.number_input("新 第2層 (%)", 0.0, 40.0, 15.0, step=0.1, format="%.1f")
    with col_r3:
        r3 = st.number_input("新 第3層 (%)", 0.0, 40.0, 10.0, step=0.1, format="%.1f")
    with col_r4:
        r4 = st.number_input("新 第4層 (%)", 0.0, 40.0, 6.0, step=0.1, format="%.1f")
    
    # 市場反応（維持率）
    st.write("**【市場の反応】**")
    retention = st.slider("想定される顧客維持率 (%)", 50.0, 100.0, 95.0, step=0.5) / 100

    """
    # --- メイン画面：改定案の作成 ---
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.write("**【境界金額の変更】**")
        b1 = st.slider("第1境界", 100, 1000, 300) * 10000
        b2 = st.slider("第2境界", 1000, 5000, 3000) * 10000
        b3 = st.slider("第3境界", 5000, 50000, 30000) * 10000
    with col_p2:
        st.write("**【改定案の割合】**")
        r1, r2, r3, r4 = [st.slider(f"新 第{i}層", 0.0, 40.0, v) for i, v in enumerate([20.0, 15.0, 10.0, 6.0], 1)]
    with col_p3:
        st.write("**【市場の反応】**")
        retention = st.slider("想定維持率 (%)", 50, 100, 95) / 100

    new_brackets = [(0, b1, r1), (b1, b2, r2), (b2, b3, r3), (b3, float('inf'), r4)]
    """

    # --- 計算と結果表示 ---
    current_total = sum(calculate_fee(r[0], current_brackets) * r[1] for r in edited_df.values)
    new_total_100 = sum(calculate_fee(r[0], new_brackets) * r[1] for r in edited_df.values)
    new_total_actual = new_total_100 * retention

    st.divider()
    res_col1, res_col2 = st.columns([2, 1])
    with res_col1:
        st.bar_chart(pd.DataFrame({"プラン": ["現状", "想定"], "報酬総額": [current_total, new_total_actual]}), x="プラン", y="報酬総額")
    with res_col2:
        diff = new_total_actual - current_total
        st.metric("想定報酬額", f"{int(new_total_actual):,}円", delta=f"{int(diff):+,}円")
        be_retention = (current_total / new_total_100) if new_total_100 > 0 else 0
        st.info(f"損益分岐: 顧客減少 {100 - be_retention*100:.1f}% まで維持可能")

    # --- 3. 詳細テーブル & CSVダウンロード機能 ---
    st.divider()
    st.subheader("🧐 報酬比較詳細データ")
    
    sample_amounts = [500_000, 1_000_000, 3_000_000, 5_000_000, 10_000_000, 30_000_000, 100_000_000]
    comparison_df = pd.DataFrame([{
        "解決金額": amt,
        "現状報酬": int(calculate_fee(amt, current_brackets)),
        "新案報酬": int(calculate_fee(amt, new_brackets)),
        "差額": int(calculate_fee(amt, new_brackets) - calculate_fee(amt, current_brackets))
    } for amt in sample_amounts])
    
    st.table(comparison_df.style.format("{:,}"))

    # CSV変換
    csv = comparison_df.to_csv(index=False).encode('utf-8-sig') # Excelで開けるようにBOM付きUTF-8
    st.download_button(
        label="📊 比較データをCSVとしてダウンロード",
        data=csv,
        file_name='lawyer_fee_comparison.csv',
        mime='text/csv',
    )
