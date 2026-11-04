# Xếp gợi ý học tập theo mức độ cần xử lý

## 1. Đọc nhanh: Chúng ta đang giải quyết điều gì?

Hệ thống cần trả lời hai câu hỏi khác nhau:

1. **Dự báo:** Sinh viên có nguy cơ trượt/bỏ học ở mức nào?
2. **Gợi ý:** Với tình trạng hiện tại, vấn đề nào cần được chú ý trước?

Ví dụ: Sinh viên có nhịp học chưa đều, nhưng đồng thời còn 5 bài chưa nộp và hạn nộp bù chỉ còn 2 ngày. Nếu hệ thống đưa "thiết lập lịch học đều đặn" lên trên "xử lý bài thiếu sát hạn", thứ tự đó chưa hợp lý.

**Mục tiêu của đề xuất là tránh những thứ tự khó chấp nhận như vậy. Không phải tìm ra một cách can thiệp chắc chắn tốt nhất cho mọi sinh viên.**

Không thể chỉ từ vài chỉ số mà biết chắc sinh viên sẽ phản ứng thế nào. Tuy nhiên, chúng ta vẫn có thể quy định những nguyên tắc rõ ràng: không bỏ qua việc gấp, không cảnh báo sai hoàn cảnh và không kết luận khi thiếu dữ kiện.

> Cách hiểu ngắn nhất: **Đúng vấn đề, đúng mức ưu tiên, biết rõ điều gì còn cần xác minh.**

## 2. Bài toán cần giải quyết

### 2.1. Đầu vào và đầu ra mong muốn

**Đầu vào:** Các chỉ số học tập của sinh viên, kết quả dự báo và những thông tin thực tế đã xác minh như số bài đến hạn, hạn nộp bù, khả năng truy cập hệ thống học tập trực tuyến (LMS).

**Đầu ra:** Một danh sách gợi ý có thể giải thích được:

- Đang có vấn đề gì?
- Vì sao vấn đề này đứng trước vấn đề kia?
- Có đủ thông tin để đề xuất hành động chưa?
- Có thể bắt đầu ngay hay còn chờ một điều kiện khác?

### 2.2. Thế nào là một kết quả hợp lý?

| Nguyên tắc | Ví dụ dễ hiểu |
| --- | --- |
| Việc gấp không bị lời khuyên dài hạn lấn lên | Xử lý bài thiếu sát hạn trước lời khuyên học đều hơn. |
| Cảnh báo phải đúng tình trạng | Đã nộp đủ bài thì không tiếp tục nhắc "nộp các bài còn thiếu". |
| Chưa biết thì xác minh | Chưa biết có bài đến hạn hay chưa thì chưa được kết luận sinh viên thiếu bài. |
| Không biến dấu hiệu thành nguyên nhân chắc chắn | Ít hoạt động trên LMS chưa chứng minh sinh viên lười học hoặc mất động lực. |
| Phân biệt quan trọng với làm được ngay | Nộp bài vẫn quan trọng, dù phải sửa lỗi truy cập trước khi nộp qua LMS. |
| Không tạo cảnh báo cho đủ số lượng | Không có vấn đề đủ căn cứ thì chỉ duy trì và theo dõi. |

## 3. Những bất cập cần khắc phục

### 3.1. Chỉ số xấu nhất không tự động là việc phải xử lý đầu tiên

Các chỉ số không cùng thang đo: số ngày ngưng hoạt động, tỷ lệ nộp bài và số lượt nhấp không thể so trực tiếp bằng cách chọn con số nhỏ nhất hoặc lớn nhất.

Ngay cả khi đã chuẩn hóa, vẫn cần ngữ cảnh. Tỷ lệ nộp bài bằng 0 có thể là thiếu toàn bộ bài đã đến hạn, nhưng cũng có thể là chưa có bài nào đến hạn hoặc dữ liệu chưa cập nhật.

**Trả lời câu hỏi ban đầu:** Gợi ý cần liên quan đến vấn đề đang có, nhưng không nhất thiết chỉ số "tệ nhất" luôn được ưu tiên đầu tiên. Phải xét thêm thời hạn, mức gián đoạn và độ đầy đủ của thông tin.

### 3.2. Mức ảnh hưởng đến dự báo khác mức cần xử lý

Trong một bản thử trước, SHAP được dùng để xếp gợi ý. Có thể hiểu SHAP là cách giải thích chỉ số nào đang góp phần làm dự báo tăng hoặc giảm.

Nhưng "chỉ số này ảnh hưởng nhiều đến dự báo" không đồng nghĩa với "hành động liên quan phải làm trước mọi hành động khác". SHAP cũng không chứng minh việc thay đổi chỉ số đó sẽ làm sinh viên học tốt hơn.

Vì vậy, không nên dùng riêng SHAP để quyết định thứ tự can thiệp.

### 3.3. Hiện trạng trên nhánh đang soạn báo cáo

Đã đối chiếu mã nguồn của nhánh `nguyengiabao`, tại commit nền `fde0a6f`. Dashboard gọi `generateInterventions` trong `apps/frontend/src/utils/recommendations.ts`.

| Điểm quan sát từ mã nguồn | Điều có thể chưa hợp lý |
| --- | --- |
| Khi sinh viên không được phân loại có nguy cơ, hàm trả về gợi ý theo dõi/duy trì ngay. | Một vấn đề cụ thể cần chú ý có thể không được xem xét, dù xác suất tổng thể chưa vượt ngưỡng phân loại. |
| Khi có nguy cơ, các gợi ý được thêm theo thứ tự các khối điều kiện; hàm không sắp xếp lại danh sách trước khi trả về. | Ví dụ, lời khuyên lập lịch học có thể đứng trước hỗ trợ nộp bài, vì được thêm trước trong mã. |
| Chưa nộp bài nào là điều kiện tạo gợi ý hỗ trợ kỹ thuật nộp bài. | Chưa có số bài đến hạn, hạn bù và xác nhận trở ngại kỹ thuật để phân biệt hoàn cảnh. |
| Một số câu mô tả diễn giải từ hoạt động LMS sang thói quen học. | Hoạt động LMS thấp chưa đủ để kết luận học dồn; sinh viên có thể học ngoài hệ thống. |

Đây là nhận xét từ việc đọc hàm hiện tại, **không phải kết quả chạy kiểm thử giao diện của nhánh này**.

**Lưu ý về các phiên bản:** Bản thử SHAP trước đó dùng bản ứng dụng trong thư mục `main_app` bên ngoài repository này. Nhánh `nguyengiabao` hiện dùng bộ quy tắc vừa mô tả, không phải bộ xếp SHAP đó. Báo cáo phân biệt hai nguồn, không gọi tất cả là cùng một "phiên bản cũ".

### 3.4. Thêm trọng số hay thêm nhiều P chưa giải quyết đúng gốc

- Một bộ trọng số có thể làm thay đổi thứ tự, nhưng các con số do chúng ta tự đặt không tự làm gợi ý đáng tin hơn.
- Nếu cộng chung các điểm, nhiều yếu tố phụ có thể đẩy một gợi ý ít quan trọng lên trên vấn đề gấp.
- Tăng từ 4 lên nhiều mức P không tự giúp nhận diện thêm tình huống. Muốn bao quát hơn phải bổ sung điều kiện, dữ kiện và cách xử lý khi chưa biết.
- Quy tắc "không vào được LMS thì luôn đứng đầu" cũng quá cứng: gọi điện cho sinh viên vẫn thực hiện được mà không cần LMS.

## 4. Giải pháp đề xuất

### 4.1. Giữ bốn mức ưu tiên, nhưng làm rõ ý nghĩa

| Mức | Ý nghĩa | Ví dụ trong bản thử |
| --- | --- | --- |
| **P1** | Cần xử lý trước | Liên hệ xác minh khi gián đoạn kéo dài; xử lý bài thiếu sát hạn bù. |
| **P2** | Cần hỗ trợ sớm | Xử lý bài thiếu khi hạn bù chưa sát; hỗ trợ quản lý hạn nộp khi liên tục nộp trễ. |
| **P3** | Cần cải thiện | Điều chỉnh nhịp học; hỗ trợ học liệu khi có nhu cầu đã xác nhận. |
| **P4** | Duy trì/theo dõi | Chưa có vấn đề đủ căn cứ để cảnh báo. |

P4 không phải một cảnh báo nhẹ được thêm vào cho đủ danh sách. Khi đã có các việc cần xử lý, không cần tự động chèn thêm P4.

Các mức này thể hiện thứ tự nghiệp vụ, **không phải phần trăm chắc chắn gợi ý đúng**.

### 4.2. Tách bốn thông tin thay vì dồn hết vào P

Một gợi ý nên mang bốn thông tin riêng:

| Thông tin | Câu hỏi cần trả lời | Ví dụ |
| --- | --- | --- |
| Loại vấn đề | Sinh viên đang gặp vấn đề gì? | Thiếu bài; gián đoạn; cần hỗ trợ học liệu. |
| Mức ưu tiên | Cần chú ý trước hay sau? | Bài thiếu sát hạn được xếp P1. |
| Thông tin cần xác minh | Chúng ta chưa biết điều gì? | Chưa biết hạn bù hoặc bài còn được tiếp nhận không. |
| Điều kiện thực hiện | Muốn làm việc này phải giải quyết gì trước? | Phải khôi phục truy cập để nộp bài qua LMS. |

Nhờ vậy, một gợi ý vẫn có thể **rất quan trọng nhưng chưa thực hiện ngay được**. Không cần hạ mức quan trọng chỉ vì đang bị chặn.

### 4.3. Luồng xử lý dễ hiểu

```text
Kiểm tra dữ liệu
  -> Xác định vấn đề có đủ căn cứ
  -> Ghi rõ điều còn chưa biết
  -> Gán P1, P2 hoặc P3 cho các gợi ý phù hợp
  -> Sắp theo mức ưu tiên
  -> Gắn điều kiện phụ thuộc và đề xuất bước tiếp theo

Nếu chưa có vấn đề đủ căn cứ: duy trì/theo dõi (P4).
Nếu thiếu dữ kiện quan trọng: yêu cầu xác minh, không tự đoán.
```

Khi hai gợi ý cùng mức P, bản thử dùng đóng góp SHAP dương lớn nhất trong nhóm vấn đề để phân thứ tự; nếu vẫn bằng nhau thì dùng mã gợi ý để thứ tự ổn định. SHAP chỉ là tiêu chí phụ, không được đẩy P3 lên trên P1. Thứ tự giữa hai việc cùng P không được coi là tối ưu đã chứng minh.

Việc dùng SHAP theo cách này thuộc bản thử; muốn đưa vào nhánh hiện tại phải bổ sung luồng giải thích tương ứng, không thể chỉ đổi nhãn trên giao diện.

### 4.4. Không cần bộ trọng số tổng hợp ở giai đoạn này

Bản đề xuất không cộng điểm theo tỷ lệ như "40% SHAP + 40% khẩn cấp + 20% khả thi".

Thay vào đó, ưu tiên cấp trước, rồi mới phân thứ tự trong cùng cấp. Cách này dễ kiểm tra hơn: một lời khuyên cải thiện không thể nhờ điểm phụ mà vượt cảnh báo cần xử lý trước.

Muốn tăng mức đáng tin của gợi ý, nên làm rõ **bằng chứng, điều kiện áp dụng, thông tin còn thiếu và lý do xếp hạng**, thay vì gắn một con số "độ uy tín" chưa được kiểm chứng.

## 5. Ba ví dụ chính

### Ví dụ 1: Cần nộp bài trước hay học đều trước?

Sinh viên An còn 5 bài đã đến hạn nhưng chưa nộp; được phép nộp bù trong 2 ngày tới. An vẫn có hoạt động học, nhưng chưa đều.

| Thứ tự minh họa chưa hợp lý | Thứ tự đề xuất |
| --- | --- |
| 1. Lập lịch học đều hơn. | 1. **P1: Hoàn thành và nộp bù bài còn thiếu.** |
| 2. Xử lý các bài chưa nộp. | 2. **P3: Thống nhất lịch học khả thi trong tuần.** |

**Vì sao?** Bài thiếu đang có hạn cụ thể. Lịch học vẫn cần cải thiện, nhưng không nên che khuất việc có thể mất cơ hội xử lý sau 2 ngày. Bảng này minh họa nguyên tắc, không phải ảnh chụp đầu ra của hai phiên bản web.

### Ví dụ 2: Không vào được LMS có luôn đứng đầu không?

Sinh viên Bình gián đoạn 30 ngày, còn 3 bài thiếu, hạn bù còn 10 ngày và đã xác nhận không truy cập được LMS.

**Theo mức quan trọng:** P1 liên hệ xác minh gián đoạn, rồi P2 xử lý bài thiếu, rồi P3 điều chỉnh lịch học.

**Trình tự đề xuất để làm được việc:**

1. Liên hệ Bình qua điện thoại/email: có thể bắt đầu ngay.
2. Hỗ trợ khôi phục truy cập LMS: điều kiện trước khi nộp qua LMS.
3. Hoàn thành/nộp bù bài: thực hiện sau khi điều kiện truy cập được giải quyết.
4. Thống nhất lịch học tiếp theo.

**Vì sao không cho sửa LMS luôn là số 1?** Liên hệ để hiểu tình trạng của Bình không phụ thuộc LMS. Nếu bài được phép nộp trực tiếp thì việc nộp cũng không phải chờ sửa LMS.

Đây là sự khác nhau giữa **"quan trọng hơn"** và **"phải làm trước để việc khác thực hiện được"**. Trình tự trên không có nghĩa mọi việc độc lập bắt buộc phải chờ nhau.

### Ví dụ 3: Tỷ lệ nộp bài bằng 0 có chắc là thiếu bài?

| Thông tin thực tế | Cách xử lý hợp lý |
| --- | --- |
| Có 5 bài đến hạn, chưa nộp bài nào. | Có căn cứ về bài thiếu; xét hạn bù để ưu tiên. |
| Chưa có bài nào đến hạn. | Không cảnh báo thiếu bài. |
| Chưa biết có bao nhiêu bài đến hạn. | Yêu cầu xác minh trước, chưa kết luận thiếu bài. |

**Cùng một con số 0 nhưng ba hoàn cảnh khác nhau.** Đây là lý do phải bổ sung ngữ cảnh, thay vì chỉ tăng số mức P.

## 6. Kết quả chạy thử

### 6.1. Cách đọc bảng

- Đây là hồ sơ giả lập, không phải sinh viên thật. Tên An/Bình ở phần ví dụ chỉ để dễ hình dung.
- "Nguy cơ" là xác suất thuộc lớp trượt/bỏ học do model dự báo, không phải tỷ lệ rớt đã quan sát và không bảo đảm tương ứng chính xác ngoài thực tế.
- Ngày hoạt động được tính trong cửa sổ 180 ngày. "Ngưng LMS" là số ngày từ hoạt động LMS gần nhất, không khẳng định sinh viên ngưng mọi hình thức học.
- Ngữ cảnh như số bài đến hạn, hạn bù và lỗi truy cập được cung cấp cho bản thử, không phải model tự suy ra.
- Các đặc trưng khác vẫn có thể ảnh hưởng đến dự báo; bảng chỉ trích chỉ số chính để dễ đọc.

### 6.2. Một số kết quả tiêu biểu

| Tình huống | Bài nộp/đến hạn | Ngày hoạt động | Ngưng LMS | Nguy cơ | Kết quả của bản thử |
| --- | --- | --- | --- | --- | --- |
| Không hoạt động; xác nhận thiếu bài; hạn bù còn 2 ngày | 0/5 | 0 | 180 ngày | 98,93% | P1 liên hệ, rồi P1 nộp bù; không thêm lời khuyên phụ cho đủ danh sách. |
| Vẫn học; thiếu toàn bộ bài; hạn bù còn 2 ngày | 0/5 | 60 | 5 ngày | 38,09% | P1 nộp bù, rồi P3 điều chỉnh lịch học. |
| Đã nộp đủ nhưng gián đoạn kéo dài | 5/5 | 60 | 21 ngày | 17,26% | P1 liên hệ, rồi P3 lịch học; không nhắc nộp bài thiếu. |
| Thiếu bài và gián đoạn; hạn bù còn 10 ngày | 2/5 | 18 | 30 ngày | 94,60% | P1 liên hệ, rồi P2 nộp bù, rồi P3 lịch học. |
| Chưa có bài nào đến hạn | 0/0 | 60 | 5 ngày | 38,09% | Không cảnh báo thiếu bài; chỉ có P3 điều chỉnh lịch học. |
| Chưa biết số bài đến hạn | 0/? | 60 | 5 ngày | 38,09% | Xác minh số bài đến hạn; chưa tạo cảnh báo thiếu bài. |
| Đã nộp đủ nhưng có 3 bài trễ | 5/5 | 140 | 0 ngày | 9,05% | P2 hỗ trợ quản lý hạn nộp tiếp theo; không yêu cầu nộp lại. |
| Học đều, đã nộp đủ | 5/5 | 140 | 0 ngày | 5,71% | P4 duy trì/theo dõi, không tạo cảnh báo. |

**Điểm cần chú ý:** Hồ sơ có nguy cơ 17,26% vẫn có thể cần P1 về gián đoạn. Ngược lại, xác suất 38,09% không phải lý do để tự kết luận thiếu bài khi chưa có bài đến hạn. Mức P gắn với vấn đề cụ thể, không phải đổi tên các khoảng xác suất.

Những hồ sơ cùng đầu vào model nhưng khác số bài đến hạn hoặc trạng thái truy cập có thể giữ nguyên xác suất mà nhận gợi ý khác. Điều này đúng với thiết kế: **không sửa dự báo để làm đẹp kết quả; chỉ bổ sung cách chọn và xếp gợi ý theo ngữ cảnh.**

### 6.3. Các tình huống dễ bị xử lý sai cũng đã được thử

| Tình huống | Cách xử lý của bản thử |
| --- | --- |
| Tất cả chỉ số hành vi bằng 0, chưa xác minh | Yêu cầu kiểm tra dữ liệu; không đưa danh sách hành động như thể tình trạng đã được xác nhận. Xác suất chạy chẩn đoán không được xem là căn cứ can thiệp đã xác minh. |
| Biết có bài thiếu nhưng chưa biết hạn bù | Yêu cầu xác minh hạn bù. P2 chỉ tạm thời, không có nghĩa đã xác nhận vấn đề không khẩn. |
| Thiếu bài sát hạn nhưng chưa rõ có lỗi truy cập không | Giữ mức quan trọng của vấn đề; xác minh truy cập, không tự kết luận có lỗi. |
| Hạn bù đã qua | Xác minh bài còn được tiếp nhận hoặc có phương án khác; không tự giả định được gia hạn. |
| Không vào được LMS nhưng được phép nộp trực tiếp | Không chặn việc nộp bằng điều kiện sửa LMS. |
| Học tốt nhưng đã xác nhận cần hỗ trợ học liệu | Đề xuất P3 hỗ trợ đúng nhu cầu, không suy diễn chỉ từ số lượt nhấp. |
| Lượt nhấp 7 ngày lớn hơn lượt nhấp 30 ngày, cùng cách đếm và thời điểm | Dừng suy luận trên dữ liệu sai và yêu cầu kiểm tra nguồn. |

## 7. Đã kiểm chứng được gì, chưa kiểm chứng được gì?

### 7.1. Kết quả kỹ thuật đã có

- Đã chạy **16 tình huống giả lập** qua bản thử độc lập.
- **67 kiểm thử đạt**, gồm 31 kiểm thử mới và 36 kiểm thử hồi quy của các bản thử trước.
- Có kiểm tra 64 tổ hợp SHAP nhằm thử việc gợi ý cấp thấp không vượt gợi ý cấp cao trong các trường hợp kiểm thử.
- Đã kiểm tra điều kiện phụ thuộc, yêu cầu xác minh và thứ tự bước tiếp theo.
- Model, mã dự báo và mã gợi ý của bản ứng dụng dùng trong thử nghiệm không đổi sau lần chạy; xác suất không đổi khi chỉ đổi ngữ cảnh mà model không nhận.

### 7.2. Giới hạn phải nói rõ

- Đây là kiểm thử tính nhất quán của quy tắc, không phải nghiên cứu chứng minh sinh viên sẽ giảm nguy cơ hoặc đậu môn sau can thiệp.
- Không có cơ sở nói độ chính xác dự báo hay độ hiệu chuẩn xác suất đã tăng. Không huấn luyện lại model.
- Một số ngưỡng đang là đề xuất nghiệp vụ: gián đoạn dài từ 14 ngày, hạn bù sát từ 2 ngày trở xuống, nộp trễ lặp lại từ 2 bài. Cần người phụ trách học phần rà soát, không xem là chuẩn chung cho mọi môn.
- Tình huống giả lập chưa bao quát mọi sinh viên và mọi cách tổ chức học phần. Đặc biệt không dùng xác suất ở mẫu cực đoan làm kết luận thực tế đã được xác nhận.
- Bộ kiểm thử chạy ở thư mục thử nghiệm, không phải bộ kiểm thử tích hợp của repository hoặc web trên nhánh này.
- Các trường ngữ cảnh bổ sung chưa nằm trong hợp đồng 17 đặc trưng dự báo của nhánh hiện tại. Muốn đưa lên web phải thiết kế nguồn dữ liệu và giá trị "chưa biết", không gán sẵn giá trị giả.

## 8. Có nên đưa lên web không?

**Đề xuất: Có thể dùng làm hướng thiết kế, nhưng chỉ tích hợp sau khi duyệt quy tắc và nguồn dữ liệu.** Chưa triển khai tự động chỉ dựa vào kết quả thử nghiệm này.

Trước khi triển khai cần thống nhất:

1. Ai cung cấp/xác nhận số bài đến hạn, hạn nộp bù, quyền nộp muộn và kênh nộp?
2. Các ngưỡng ưu tiên có phù hợp từng học phần không?
3. Web trình bày thế nào khi dữ kiện thiếu, ưu tiên chỉ tạm thời hoặc hành động đang bị chặn?
4. Các trường hợp mẫu có giữ đúng thứ tự sau khi nối vào dữ liệu và giao diện thật không?

Mỗi gợi ý trên web nên hiển thị tối thiểu: **việc cần làm, mức P, lý do, điều cần xác minh và trạng thái có thể bắt đầu**. Đây là nội dung giao diện đề xuất, chưa phải tính năng đã triển khai.

Không cần thêm nhiều P lúc này. Khi phát sinh tình huống mới, trước tiên xem đó là **loại vấn đề mới, dữ kiện mới hay điều kiện phụ thuộc mới**. Chỉ thêm cấp ưu tiên nếu thực sự có một mức xử lý khác biệt mà bốn mức hiện tại không thể diễn đạt.

## 9. Nội dung xin duyệt

- [ ] Chốt mục tiêu: hợp lý và giải thích được, không tuyên bố tối ưu hành vi con người.
- [ ] Chốt P1-P4; P4 là duy trì/theo dõi, không phải cảnh báo được tạo thêm.
- [ ] Chốt không dùng tổng điểm trọng số ở giai đoạn này; SHAP chỉ phụ trợ trong cùng cấp ở bản thử.
- [ ] Chốt nguyên tắc không đoán dữ kiện thiếu và tách điều kiện thực hiện khỏi mức quan trọng.
- [ ] Duyệt ví dụ, ngưỡng thử nghiệm và định hướng lấy dữ liệu trước khi quyết định tích hợp web.

**Kết luận:** Giá trị của đề xuất không nằm ở việc có nhiều mức P hay công thức nhiều trọng số. Giá trị nằm ở việc **cảnh báo quan trọng không bị lời khuyên phụ lấn lên, gợi ý đúng hoàn cảnh và người xem hiểu vì sao hệ thống đề xuất như vậy**.

## Phụ lục: Nguồn đối chiếu

- Nhánh tài liệu: `nguyengiabao`; commit nền lúc soạn: `fde0a6f`.
- Hiện trạng nhánh: `apps/frontend/src/utils/recommendations.ts`, `apps/frontend/src/pages/DashboardPage.tsx`, `apps/backend/schemas/prediction.py`.
- Bản thử độc lập: `C:\Users\nguye\.codex\visualizations\2026\11\04\01a1a6f1-6c66-7020-82ca-d71139deff16\ranking-lab`.
- Trong thư mục thử: `context_trial.py`, `test_context_trial.py`, `output-context/results.json`, `output-context/report.md`, `output-context/verification.json`, `output-context/test-results.txt`.
- Lần chạy kết quả được trích: 23:10:44 ngày 04/11/2026, múi giờ +07:00.
- Thử nghiệm dùng model trong thư mục `ChienLuocHocTap\main_app` ngoài repository. Đã đối chiếu model đó và model trên nhánh có cùng SHA-256: `90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db`. Cùng model không có nghĩa hai bộ mã ứng dụng giống nhau.
- Đường dẫn thử nghiệm là vị trí trên máy soạn, không phải tài nguyên đã đưa vào Git. Các con số kiểm thử được trích từ đầu ra đã có; lần soạn tài liệu này không chạy lại thử nghiệm hoặc thay đổi ứng dụng.
