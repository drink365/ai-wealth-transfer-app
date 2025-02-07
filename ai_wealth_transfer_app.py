# （前面的公開區域程式碼...）

# ===============================
# 受保護區域：模擬試算與效益評估（僅限授權使用者）
# ===============================
with st.container():
    st.markdown("## 模擬試算與效益評估 (僅限授權使用者)")
    
    # 確保引用全域變數 config
    global config
    
    # 如果尚未在 st.session_state 中記錄 authenticated 狀態，初始化為 False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # 重新初始化一個受保護區域的 authenticator 物件
        authenticator_protected = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        protected_fields = {"username": "帳號", "password": "密碼", "login_button": "登入以檢視詳細模擬結果"}
        name, authentication_status, username = authenticator_protected.login(fields=protected_fields)
        if authentication_status:
            st.session_state.authenticated = True
            st.success(f"登入成功！歡迎 {name}")
        else:
            st.info("請先登入以檢視模擬試算與效益評估區域內容。")
            st.stop()
    
    # 以下為受保護區域的商業邏輯（例如：模擬試算與效益評估）...
    st.markdown("這裡顯示受保護區域的模擬試算與效益評估結果……")
    
    # 若需要登出按鈕，可以呼叫：
    authenticator_protected.logout("登出", "sidebar")
