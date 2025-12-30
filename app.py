import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

# --- 1. 기본 설정 및 데이터 ---
st.set_page_config(layout="wide", page_title="치전원 자봉 관리")

# [학생 명단 및 기존 점수 관리]
STUDENTS = {
    1: {"name": "강동우", "base_score": 0},
    2: {"name": "강라원", "base_score": 0},
    3: {"name": "강수지", "base_score": 0},
    4: {"name": "고준희", "base_score": 0},
    5: {"name": "곽채린", "base_score": 0},
    6: {"name": "김가윤", "base_score": 0},
    7: {"name": "김건희", "base_score": 0},
    8: {"name": "김다은", "base_score": 0},
    9: {"name": "김동한", "base_score": 0},
    10: {"name": "김명성", "base_score": 0},
    11: {"name": "김민경", "base_score": 0},
    12: {"name": "김부미", "base_score": 0},
    13: {"name": "김사희", "base_score": 0},
    14: {"name": "김신찬", "base_score": 0},
    15: {"name": "김연규", "base_score": 0},
    16: {"name": "김유정", "base_score": 0},
    17: {"name": "김인기", "base_score": 0},
    18: {"name": "나은서", "base_score": 0},
    19: {"name": "나현진", "base_score": 0},
    20: {"name": "노은재", "base_score": 0},
    21: {"name": "문예린", "base_score": 0},
    22: {"name": "민지호", "base_score": 0},
    23: {"name": "박상욱", "base_score": 0},
    24: {"name": "박상희", "base_score": 0},
    25: {"name": "박세준", "base_score": 0},
    26: {"name": "박찬서", "base_score": 0},
    27: {"name": "백인경", "base_score": 0},
    28: {"name": "석승헌", "base_score": 0},
    29: {"name": "석재민", "base_score": 0},
    30: {"name": "송상욱", "base_score": 0},
    31: {"name": "송지연", "base_score": 0},
    32: {"name": "송창영", "base_score": 0},
    33: {"name": "신하은", "base_score": 0},
    34: {"name": "안성원", "base_score": 0},
    35: {"name": "양산업", "base_score": 0},
    36: {"name": "염규정", "base_score": 0},
    37: {"name": "오승아", "base_score": 0},
    38: {"name": "오승우", "base_score": 0},
    39: {"name": "오지희", "base_score": 0},
    40: {"name": "유복원", "base_score": 0},
    41: {"name": "유성빈", "base_score": 0},
    42: {"name": "이기훈", "base_score": 0},
    43: {"name": "이민재", "base_score": 0},
    44: {"name": "이성현", "base_score": 0},
    45: {"name": "이수현", "base_score": 0},
    46: {"name": "이승재", "base_score": 0},
    47: {"name": "이완규", "base_score": 0},
    48: {"name": "이재강", "base_score": 0},
    49: {"name": "이주호", "base_score": 0},
    50: {"name": "이희진", "base_score": 0},
    51: {"name": "임성영", "base_score": 0},
    52: {"name": "장유나", "base_score": 0},
    53: {"name": "장유리", "base_score": 0},
    54: {"name": "장은빈", "base_score": 0},
    55: {"name": "전현도", "base_score": 0},
    56: {"name": "정성훈", "base_score": 0},
    57: {"name": "정원찬", "base_score": 0},
    58: {"name": "정재원", "base_score": 0},
    59: {"name": "정주희", "base_score": 0},
    60: {"name": "정준혁", "base_score": 0},
    61: {"name": "조경빈", "base_score": 0},
    62: {"name": "조성훈", "base_score": 0},
    63: {"name": "최다은", "base_score": 0},
    64: {"name": "최윤혁", "base_score": 0},
    65: {"name": "한석희", "base_score": 0},
    66: {"name": "현지은", "base_score": 0},
    67: {"name": "황솔빈", "base_score": 0},
}
student_options = [f"{num}. {info['name']}" for num, info in STUDENTS.items()]

# --- 2. 구글 시트 연결 ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if os.path.exists("service_account.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    elif "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        st.error("인증 파일을 찾을 수 없습니다.")
        st.stop()
        
    client = gspread.authorize(creds)
    spreadsheet = client.open("jabong_db")
    sheet_log = spreadsheet.worksheet("log")
    sheet_matrix = spreadsheet.worksheet("matrix")
    sheet_history = spreadsheet.worksheet("history")
    
    try:
        sheet_legacy = spreadsheet.worksheet("기존자봉")
    except:
        sheet_legacy = None

except Exception as e:
    st.error(f"구글 시트 연결 오류: {e}")
    st.stop()

# --- 함수: 숫자 포맷팅 ---
def smart_format(x):
    try:
        f = float(x)
        if f.is_integer():
            return int(f)
        return f
    except:
        return x

# --- 함수: 매트릭스 시트 업데이트 ---
def update_google_sheet_matrix(df_log):
    master_data = [{"번호": k, "이름": v['name']} for k, v in STUDENTS.items()]
    df_master = pd.DataFrame(master_data)

    if sheet_legacy:
        legacy_data = sheet_legacy.get_all_records()
        df_legacy = pd.DataFrame(legacy_data)
        if not df_legacy.empty:
            df_legacy['번호'] = pd.to_numeric(df_legacy['번호'], errors='coerce')
            score_col = '기존점수' if '기존점수' in df_legacy.columns else df_legacy.columns[2]
            df_legacy[score_col] = pd.to_numeric(df_legacy[score_col], errors='coerce').fillna(0)
            df_legacy = df_legacy.rename(columns={score_col: '기존점수'})
            df_master = pd.merge(df_master, df_legacy[['번호', '기존점수']], on='번호', how='left')
        else:
            df_master['기존점수'] = 0
    else:
        df_master['기존점수'] = [STUDENTS[k]['base_score'] for k in STUDENTS]
    
    df_master['기존점수'] = df_master['기존점수'].fillna(0)

    if not df_log.empty:
        df_log['점수'] = pd.to_numeric(df_log['점수'], errors='coerce').fillna(0)
        df_log['번호'] = pd.to_numeric(df_log['번호'], errors='coerce')
        total = df_log.groupby('번호')['점수'].sum().reset_index()
        total.columns = ['번호', '신규합계']
        pivot = df_log.pivot_table(index='번호', columns='날짜', values='점수', aggfunc='sum', fill_value=0)
        
        df_merged = pd.merge(df_master, total, on='번호', how='left')
        df_final = pd.merge(df_merged, pivot, on='번호', how='left')
    else:
        df_final = df_master.copy()
        df_final['신규합계'] = 0

    df_final = df_final.fillna(0)
    df_final['총점'] = df_final['기존점수'] + df_final['신규합계']
    
    fixed_cols = ['번호', '이름', '기존점수', '총점']
    date_cols = sorted([c for c in df_final.columns if c not in fixed_cols and c != '신규합계'])
    df_final = df_final[fixed_cols + date_cols]

    for col in df_final.columns:
        if col != "이름":
            df_final[col] = df_final[col].apply(smart_format)

    headers = df_final.columns.tolist()
    values = df_final.astype(str).values.tolist()
    sheet_matrix.clear()
    sheet_matrix.update(range_name='A1', values=[headers] + values)

# --- 함수: 이력(History) 남기기 ---
def log_history(action_type, row_data, audit_reason, new_data=None):
    timestamp = str(datetime.now())
    target_date = row_data['날짜']
    student_name = row_data['이름']
    old_score = smart_format(row_data['점수'])
    before_str = f"[{row_data['구분']}] {row_data['사유']} ({old_score}점)"
    after_str = "-"
    if new_data:
        new_score_val = smart_format(new_data['점수'])
        after_str = f"[{new_data['구분']}] {new_data['사유']} ({new_score_val}점)"
    sheet_history.append_row([timestamp, action_type, target_date, student_name, before_str, after_str, audit_reason])

# --- 메인 화면 ---
st.title("🦷 1학년 자봉 관리 시스템")
tab1, tab2, tab3, tab4 = st.tabs(["✍️ 점수 입력", "📊 전체 현황판", "📢 공지 생성", "🛠️ 일괄 수정/삭제"])

# TAB 1: 점수 입력
with tab1:
    st.subheader("여러 명에게 한 번에 점수 부여하기")
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        target_date = col1.date_input("날짜 선택", datetime.now())
        
        st.markdown("**학생 번호 입력** (띄어쓰기나 쉼표로 구분)")
        input_nums_str = st.text_input("예: 1, 5, 12", placeholder="번호를 입력하세요")
        
        target_ids = []
        valid_names = []
        if input_nums_str:
            parts = input_nums_str.replace(',', ' ').split()
            for p in parts:
                if p.isdigit():
                    num = int(p)
                    if num in STUDENTS:
                        target_ids.append(num)
                        valid_names.append(f"{STUDENTS[num]['name']}({num})")
        
        if valid_names:
            st.info(f"선택된 학생 ({len(valid_names)}명): {', '.join(valid_names)}")
        elif input_nums_str:
            st.warning("유효한 학생 번호가 없습니다.")

        col3, col4 = st.columns(2)
        category = col3.radio("구분", ["자봉(+)", "상점(-)"], horizontal=True)
        input_score = col4.number_input("점수 (숫자만 입력)", value=1.0, step=0.1, format="%.1f")
        reason = st.text_input("사유 입력", placeholder="예: 지각, 청소")
        
        submitted = st.form_submit_button("저장 및 매트릭스 업데이트")
        
        if submitted:
            if input_score == 0:
                st.error("⚠️ 점수는 0점일 수 없습니다.")
            elif not target_ids:
                st.error("학생 번호를 올바르게 입력해주세요.")
            else:
                final_score = abs(input_score) if "자봉" in category else -abs(input_score)
                new_rows = []
                date_str = str(target_date)
                progress_text = "기록 저장 중..."
                my_bar = st.progress(0, text=progress_text)

                for i, num in enumerate(target_ids):
                    name = STUDENTS[num]['name']
                    row = [date_str, num, name, category, final_score, reason]
                    new_rows.append(row)
                    my_bar.progress((i + 1) / len(target_ids), text=progress_text)
                
                sheet_log.append_rows(new_rows)
                try:
                    update_google_sheet_matrix(pd.DataFrame(sheet_log.get_all_records()))
                    my_bar.empty()
                    st.success(f"✅ {len(new_rows)}명 저장 완료! ({', '.join(valid_names)})")
                except Exception as e:
                    st.warning(f"저장 성공, 매트릭스 갱신 오류: {e}")

# TAB 2: 현황판
with tab2:
    st.subheader("실시간 엑셀 매트릭스 조회")
    if st.button("🔄 새로고침", key='refresh_matrix'):
        st.cache_data.clear()
    matrix_data = sheet_matrix.get_all_values()
    if len(matrix_data) > 1:
        st.dataframe(pd.DataFrame(matrix_data[1:], columns=matrix_data[0]), hide_index=True, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

# TAB 3: 공지 생성
with tab3:
    st.subheader("📢 상세 공지 문구")
    notice_date = st.date_input("공지 날짜", datetime.now(), key='notice_date')
    if st.button("공지 만들기"):
        data = sheet_log.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df['날짜'] = df['날짜'].astype(str)
            df['번호'] = pd.to_numeric(df['번호'], errors='coerce')
            target_df = df[df['날짜'] == str(notice_date)]
            if not target_df.empty:
                text = f"📢 [{notice_date}] 자봉/상점 현황\n" + "=" * 25 + "\n"
                for cat in sorted(target_df['구분'].unique(), reverse=True):
                    groups = target_df[target_df['구분'] == cat].groupby(['사유', '점수'])
                    for (reason_val, score_val), group in groups:
                        nums = sorted(group['번호'].astype(int).unique())
                        nums_str = ", ".join(map(str, nums))
                        score_disp = f"+{smart_format(score_val)}" if score_val > 0 else f"{smart_format(score_val)}"
                        text += f"[{cat}] {reason_val} ({score_disp}점) : {nums_str}\n"
                text += "=" * 25 + "\n"
                text += "✅ 본인 점수 확인 및 이의신청은\n개인톡 부탁드립니다."
                st.text_area("복사용 텍스트", text, height=300)
            else:
                st.warning("해당 날짜의 기록이 없습니다.")
        else:
            st.warning("데이터가 없습니다.")

# TAB 4: 일괄 수정 및 삭제 (검색 기능 강화됨)
with tab4:
    st.subheader("🛠️ 일괄 수정 및 삭제 (조건 검색)")
    
    # 1. 필터 UI (날짜, 학생)
    col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
    
    with col_s1:
        use_all_dates = st.checkbox("전체 기간 조회")
    
    with col_s2:
        search_date = st.date_input("날짜", datetime.now(), disabled=use_all_dates, key='edit_date')
        
    with col_s3:
        search_student_str = st.selectbox("학생 선택", ["전체 학생"] + student_options, key='edit_student')
    
    # 2. 검색 실행
    if st.button("기록 불러오기"):
        data = sheet_log.get_all_records()
        df = pd.DataFrame(data)
        
        if not df.empty:
            df['row_num'] = df.index + 2
            df['날짜'] = df['날짜'].astype(str)
            
            # 필터링 로직
            mask = pd.Series([True] * len(df)) # 일단 모두 선택
            
            # 날짜 필터 (체크 안 되어 있으면 날짜로 거름)
            if not use_all_dates:
                mask = mask & (df['날짜'] == str(search_date))
                
            # 학생 필터 (전체 학생이 아니면 이름으로 거름)
            if search_student_str != "전체 학생":
                # "1. 강동우" -> "강동우" 추출
                target_name = search_student_str.split(". ")[1]
                mask = mask & (df['이름'] == target_name)
            
            filtered_df = df[mask].copy()
            st.session_state['edit_df'] = filtered_df
        else:
            st.warning("데이터가 없습니다.")
            st.session_state['edit_df'] = pd.DataFrame()

    # 3. 결과 표시 및 편집
    if 'edit_df' in st.session_state and not st.session_state['edit_df'].empty:
        edit_df = st.session_state['edit_df']
        if '선택' not in edit_df.columns:
            edit_df.insert(0, '선택', False)
        
        msg_date = "전체 기간" if use_all_dates else str(search_date)
        msg_student = search_student_str
        st.markdown(f"🔎 검색 결과 ({msg_date}, {msg_student}): **총 {len(edit_df)}건**")
        
        edited_df = st.data_editor(
            edit_df,
            hide_index=True,
            column_config={"선택": st.column_config.CheckboxColumn(required=True), "row_num": None},
            disabled=["날짜", "번호", "이름", "구분", "점수", "사유"],
            key="editor",
            use_container_width=True
        )
        
        selected_rows = edited_df[edited_df['선택'] == True]
        
        if not selected_rows.empty:
            st.info(f"총 {len(selected_rows)}개의 기록이 선택되었습니다.")
            st.markdown("---")
            
            tab_edit, tab_del = st.tabs(["✏️ 선택 항목 일괄 수정", "🗑️ 선택 항목 일괄 삭제"])
            
            with tab_edit:
                with st.form("batch_update_form"):
                    st.write("#### 1. 학생부에 기록될 내용 (변경 후)")
                    u_cat = st.radio("변경할 구분", ["자봉(+)", "상점(-)"], horizontal=True)
                    u_score = st.number_input("변경할 점수 (절대값)", value=1.0, step=0.1, format="%.1f")
                    u_reason = st.text_input("사유", placeholder="예: 지각")
                    st.write("#### 2. 관리자 기록용")
                    u_audit_reason = st.text_input("수정 이유", placeholder="예: 교수님 출결 정정 요청")
                    
                    if st.form_submit_button("일괄 수정 실행"):
                        if u_score == 0:
                            st.error("⚠️ 점수는 0점일 수 없습니다.")
                        elif not u_audit_reason:
                            st.error("⚠️ 수정을 진행하려면 '수정 이유'를 반드시 적어야 합니다.")
                        else:
                            final_u_score = abs(u_score) if "자봉" in u_cat else -abs(u_score)
                            progress = st.progress(0)
                            for idx, (i, row) in enumerate(selected_rows.iterrows()):
                                row_num = row['row_num']
                                new_data = {'구분': u_cat, '점수': final_u_score, '사유': u_reason}
                                log_history("수정", row, u_audit_reason, new_data)
                                sheet_log.update_cell(row_num, 4, u_cat)
                                sheet_log.update_cell(row_num, 5, final_u_score)
                                sheet_log.update_cell(row_num, 6, u_reason)
                                progress.progress((idx + 1) / len(selected_rows))
                            update_google_sheet_matrix(pd.DataFrame(sheet_log.get_all_records()))
                            st.success("수정 완료!")
                            del st.session_state['edit_df']

            with tab_del:
                st.write("#### 관리자 기록용")
                d_audit_reason = st.text_input("삭제 이유", placeholder="예: 중복 입력")
                st.warning("이유를 입력하고 아래 버튼을 누르면 즉시 삭제됩니다.")
                if st.button("일괄 삭제 실행", type="primary"):
                    if not d_audit_reason:
                        st.error("⚠️ 삭제를 진행하려면 '삭제 이유'를 반드시 적어야 합니다.")
                    else:
                        rows_to_delete = sorted(selected_rows['row_num'].tolist(), reverse=True)
                        progress = st.progress(0)
                        for idx, r_num in enumerate(rows_to_delete):
                            target_row_data = selected_rows[selected_rows['row_num'] == r_num].iloc[0]
                            log_history("삭제", target_row_data, d_audit_reason)
                            sheet_log.delete_rows(r_num)
                            progress.progress((idx + 1) / len(rows_to_delete))
                        update_google_sheet_matrix(pd.DataFrame(sheet_log.get_all_records()))
                        st.success("삭제 완료!")
                        del st.session_state['edit_df']
        else:
            st.write("👆 위 표에서 수정/삭제할 학생의 체크박스를 선택해주세요.")
            
    elif 'edit_df' in st.session_state:
        st.info("검색된 결과가 없습니다.")
