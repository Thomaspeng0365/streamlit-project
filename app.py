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

def is_email_already_registered(sheet, email):
    """檢查電子郵件是否已存在於 Google Sheet 中。"""
    try:
        emails_list = sheet.col_values(2)
        return email in emails_list
    except Exception as e:
        st.error(f"檢查重複電子郵件時發生錯誤：{e}")
        return False

def get_sheet_data():
    """連接並取得 Google Sheet 的資料。"""
    try:
        worksheet = gc.open("抽獎名單").sheet1
        return worksheet
    except Exception as e:
        st.error(f"無法開啟 Google Sheet。請確認服務帳號已獲得編輯權限。錯誤：{e}")
        return None

def draw_winners(df, num_winners):
    """從 DataFrame 中隨機選出指定數量的得獎者。"""
    if df.empty or num_winners <= 0:
        return None
    return random.sample(df.to_dict('records'), min(num_winners, len(df)))

def update_winners_status(sheet, winners):
    """將中獎者在 Google Sheet 中的狀態更新為 '是'。"""
    try:
        emails_list = sheet.col_values(2)
        header_row = sheet.row_values(1)
        try:
            status_col = header_row.index('是否中獎') + 1
        except ValueError:
            st.error("Google Sheet 中找不到 '是否中獎' 欄位。請先手動新增此欄位。")
            return

        for winner in winners:
            try:
                row_index = emails_list.index(winner['電子郵件']) + 1
                sheet.update_cell(row_index, status_col, "是")
            except ValueError:
                st.warning(f"找不到電子郵件為 '{winner['電子郵件']}' 的參與者，無法更新狀態。")
        
        st.success("🎉 中獎者的狀態已成功註記於 Google Sheet！")
    except Exception as e:
        st.error(f"更新 Google Sheet 時發生錯誤：{e}")


def main():
    st.sidebar.title("導航")
    mode = st.sidebar.radio("選擇模式", ["報名頁面", "管理者抽獎頁面"])

    # 使用 session_state 來儲存登入狀態
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if mode == "報名頁面":
        st.title("抽獎活動報名表單")
        st.info("請填寫您的資訊，以便參與抽獎！")

        with st.form(key="registration_form"):
            name = st.text_input("姓名")
            email = st.text_input("電子郵件")
            submit_button = st.form_submit_button("提交報名")
        
        if submit_button:
            if not name or not email:
                st.error("姓名和電子郵件為必填欄位。")
            else:
                sheet = get_sheet_data()
                if sheet:
                    if is_email_already_registered(sheet, email):
                        st.warning("您使用的電子郵件已報名過，請勿重複提交。")
                    else:
                        sheet.append_row([name, email])
                        st.success("報名成功！感謝您的參與！")
                        st.balloons()

    elif mode == "管理者抽獎頁面":
        # 如果使用者尚未登入
        if not st.session_state.logged_in:
            with st.form(key="admin_login_form"):
                st.subheader("管理者登入")
                password = st.text_input("輸入密碼", type="password")
                login_button = st.form_submit_button("登入")

            if login_button:
                if password == st.secrets.get("admin_password"):
                    st.session_state.logged_in = True
                    st.success("登入成功！")
                    # 重新執行以顯示抽獎控制台
                    st.rerun()
                else:
                    st.error("密碼錯誤。")
        else:
            # 登入成功後顯示的抽獎頁面
            st.title("管理者專屬：抽獎控制台")
            
            sheet = get_sheet_data()
            if sheet:
                data = sheet.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    
                    # 篩選出尚未中獎的參與者
                    eligible_df = df[df['是否中獎'] != '是']
                    
                    st.markdown(f"### 目前共有 {len(eligible_df)} 位合格參與者：")
                    st.dataframe(eligible_df)

                    if not eligible_df.empty:
                        num_winners = st.number_input(
                            "請輸入要抽出的得獎者人數：", 
                            min_value=1, 
                            max_value=len(eligible_df), 
                            value=1, 
                            step=1
                        )
                    
                        if st.button("開始抽獎！"):
                            if num_winners > 0 and num_winners <= len(eligible_df):
                                with st.spinner("正在抽出幸運兒..."):
                                    time.sleep(2)
                                    winners = draw_winners(eligible_df, num_winners)
                                    
                                    if winners:
                                        st.balloons()
                                        st.success("🎉🎉🎉 恭喜以下幸運兒！ 🎉🎉🎉")
                                        for winner in winners:
                                            st.success(f"**姓名**：{winner['姓名']}")
                                            st.write(f"**聯絡信箱**：{winner['電子郵件']}")
                                        st.success("🎉🎉🎉")
                                        
                                        update_winners_status(sheet, winners)
                                    else:
                                        st.error("抽獎失敗，請確認名單。")
                            else:
                                st.error("抽獎人數必須大於 0 且不超過合格參與者總數。")
                    else:
                        st.warning("目前沒有任何合格的參與者，所有人都已經中過獎。")
                else:
                    st.warning("目前沒有任何參與者報名。")

if __name__ == "__main__":
    main()
