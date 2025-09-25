import streamlit as st
import gspread
import pandas as pd
import random
import time

# 從 Streamlit secrets 讀取 Google 服務帳號憑證
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
except Exception as e:
    st.error(f"無法連接到 Google Sheets。請檢查 .streamlit/secrets.toml 檔案和服務帳號權限。錯誤：{e}")
    st.stop()

def get_sheet_data():
    """連接並取得 Google Sheet 的資料。"""
    # 開啟你的 Google Sheet，請將 '抽獎名單' 替換為你的表格名稱
    try:
        worksheet = gc.open("抽獎名單").sheet1
        return worksheet
    except Exception as e:
        st.error(f"無法開啟 Google Sheet。請確認服務帳號已獲得編輯權限。錯誤：{e}")
        return None

def draw_winner(df):
    """從 DataFrame 中隨機選出一位得獎者。"""
    if df.empty:
        return None
    return random.choice(df.to_dict('records'))

def main():
    st.sidebar.title("導航")
    mode = st.sidebar.radio("選擇模式", ["報名頁面", "管理者抽獎頁面"])

    if mode == "報名頁面":
        st.title("抽獎活動報名表單")
        st.info("請填寫您的資訊，以便參與抽獎！")

        with st.form(key="registration_form"):
            name = st.text_input("姓名")
            email = st.text_input("電子郵件")
            submit_button = st.form_submit_button("提交報名")

        if submit_button:
            if name and email:
                sheet = get_sheet_data()
                if sheet:
                    # 將新資料新增到 Google Sheet 的新一行
                    sheet.append_row([name, email])
                    st.success("報名成功！感謝您的參與！")
                    st.balloons()
            else:
                st.error("姓名和電子郵件為必填欄位。")

    elif mode == "管理者抽獎頁面":
        password = st.sidebar.text_input("輸入密碼", type="password")

        if password == st.secrets.get("admin_password"):
            st.title("管理者專屬：抽獎控制台")

            sheet = get_sheet_data()
            if sheet:
                # 讀取所有行，並轉換成 DataFrame
                data = sheet.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    st.markdown(f"### 目前共有 {len(df)} 位參與者：")
                    st.dataframe(df)

                    if st.button("開始抽獎！"):
                        with st.spinner("正在抽出幸運兒..."):
                            time.sleep(2)
                            winner = draw_winner(df)

                            if winner:
                                st.balloons()
                                st.success("🎉🎉🎉")
                                st.success(f"恭喜！本次的幸運兒是： **{winner['姓名']}**")
                                st.success(f"聯絡信箱：{winner['電子郵件']}")
                                st.success("🎉🎉🎉")
                            else:
                                st.error("抽獎失敗，請確認名單。")
                else:
                    st.warning("目前沒有任何參與者報名。")
        else:
            st.error("密碼錯誤。")

if __name__ == "__main__":
    main()