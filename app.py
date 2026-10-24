import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("Công cụ Sàng lọc Thalassemia & Phân tích Huyết học")
st.markdown("Đề tài NCKH Tin sinh học | Khoa Công nghệ Sinh học - ĐH Đồng Tháp")

# 1. Khu vực tải file lên
uploaded_file = st.file_uploader("Tải lên tập dữ liệu của bạn (CSV hoặc Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Đọc file CSV hoặc Excel
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Tự động làm sạch tên cột
        df.columns = [str(col).strip().upper() for col in df.columns]

        # Tìm các cột quan trọng
        mcv_col = next((col for col in df.columns if 'MCV' in col), None)
        rbc_col = next((col for col in df.columns if 'RBC' in col), None)

        if not mcv_col or not rbc_col:
            st.error(f"❌ File của bạn đang thiếu cột MCV hoặc RBC. Vui lòng kiểm tra lại file Excel/CSV!")
        else:
            # Ép kiểu dữ liệu sang số để tránh lỗi ký tự lạ
            df[mcv_col] = pd.to_numeric(df[mcv_col], errors='coerce')
            df[rbc_col] = pd.to_numeric(df[rbc_col], errors='coerce')

            # Tính chỉ số Mentzer Index
            df['MENTZER_INDEX'] = df[mcv_col] / df[rbc_col]
            
            # Hàm phân loại thông minh: Chỉ cần có ô nào trống (NaN/None) hoặc thiếu chỉ số là báo ERROR
            def classify_screening(row):
                # Kiểm tra toàn bộ các giá trị trong hàng xem có ô nào bị trống (None / NaN) không
                if row.isna().any():
                    return "ERROR"
                
                mcv = row.get(mcv_col, None)
                rbc = row.get(rbc_col, None)
                
                if rbc is None or rbc == 0 or pd.isna(mcv) or pd.isna(rbc):
                    return "ERROR"
                
                mentzer = mcv / rbc
                
                # Tìm các cột phụ nếu có
                mch_col = next((col for col in df.columns if 'MCH' in col and 'MCHC' not in col), None)
                rdw_col = next((col for col in df.columns if 'RDW' in col), None)
                
                mch = row.get(mch_col, None) if mch_col else None
                rdw = row.get(rdw_col, None) if rdw_col else None
                
                if mentzer < 13:
                    return "🔴 Nghi ngờ Thalassemia (Hồng cầu nhỏ)"
                elif (not pd.isna(mcv) and mcv < 80.0) or (mch is not None and not pd.isna(mch) and mch < 27.0):
                    if rdw is not None and not pd.isna(rdw) and rdw > 14.5:
                        return "🟡 Nghi ngờ Thiếu máu thiếu sắt (RDW tăng)"
                    else:
                        return "🟡 Nghi ngờ Thiếu máu thiếu sắt"
                else:
                    return "🟢 Bình thường (Normal)"
          # Gán kết quả vào bảng
            df['GỢI Ý SÀNG LỌC'] = df.apply(classify_screening, axis=1)
            
            # 2. Hiển thị bảng kết quả
            st.subheader("📋 Kết quả Sàng lọc Tự động & Quét lỗi dữ liệu")
            
            # Hàm quét lỗi và tô vàng nguyên hàng
            def highlight_error_rows(row):
                has_error = False
                
                # Kiểm tra toàn bộ các cột trong hàng xem có chứa giá trị None, NaN, hoặc rỗng không
                for val in row:
                    if pd.isna(val) or str(val).strip().lower() in ['none', 'nan', '']:
                        has_error = True
                        break
                
                # Hoặc nếu cột GỢI Ý có chữ ERROR
                if "ERROR" in str(row.get('GỢI Ý SÀNG LỌC', '')):
                    has_error = True
                
                # Khởi tạo style mặc định cho từng ô trong hàng
                styles = ['' for _ in row.index]
                
                if has_error:
                    # Tô vàng toàn bộ các ô trong hàng
                    styles = ['background-color: #fff9c4' for _ in row.index]
                    
                    # Riêng cột GỢI Ý SÀNG LỌC: Đổi chữ thành màu đỏ đậm và in đậm
                    if 'GỢI Ý SÀNG LỌC' in row.index:
                        idx = row.index.get_loc('GỢI Ý SÀNG LỌC')
                        styles[idx] = 'background-color: #fff9c4; color: #d32f2f; font-weight: bold;'
                        
                return styles

            # Lấy danh sách các cột số để làm tròn gọn gàng
            numeric_cols = df.select_dtypes(include=['float64', 'float32']).columns

            # Áp dụng style tô màu VÀ format làm tròn gọn gàng 2 chữ số thập phân
            styled_df = df.style.apply(highlight_error_rows, axis=1).format(precision=2, subset=numeric_cols)
            
            # Hiển thị lên Streamlit
            st.dataframe(styled_df, use_container_width=True)
            # Thống kê cảnh báo
            num_error = len(df[df['GỢI Ý SÀNG LỌC'] == "ERROR"])
            num_thal = len(df[df['MENTZER_INDEX'] < 13])
            
            if num_error > 0:
                st.warning(f"⚠️ Phát hiện **{num_error}** trường hợp thiếu dữ liệu (Đã tô vàng nguyên hàng và gắn nhãn ERROR đỏ).")
            
            st.info(f"ℹ️ Phát hiện **{num_thal}** trường hợp có chỉ số Mentzer < 13 cần lưu ý sàng lọc Thalassemia.")
            # 3. Trực quan hóa Biểu đồ hộp (Boxplot)
            st.subheader("📊 Trực quan hóa Biểu đồ Hộp (Boxplot) Huyết học")
            
            fig, ax = plt.subplots(figsize=(10, 5))
            mutation_col = next((col for col in df.columns if 'MUTATION' in col or 'NHOM' in col), None)
            
            if mutation_col:
                sns.boxplot(x=mutation_col, y=mcv_col, data=df, palette='Set2', ax=ax)
                plt.xticks(rotation=0, ha='center', fontsize=10)
            else:
                sns.boxplot(y=df[mcv_col], color='skyblue', ax=ax)
                
            ax.set_title("Phân bố thể tích hồng cầu trung bình (MCV)", fontsize=14, pad=15)
            ax.set_xlabel("Nhóm phân loại", fontsize=11, labelpad=10)
            ax.set_ylabel("MCV (fl)", fontsize=11)
            
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
