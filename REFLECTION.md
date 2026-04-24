# REFLECTION - Privacy, Safety, Limitations

## 1. Memory nào giúp agent nhất?

Trong ứng dụng tâm sự thông minh, memory hữu ích nhất là kết hợp giữa `long-term profile` và `episodic memory`.

`long-term profile` giúp agent nhớ các fact bền vững như tên, dị ứng, tone người dùng muốn nhận, hoặc kiểu hỗ trợ họ thấy dễ chịu. Ví dụ: nếu user nói "tôi thích được nói chuyện nhẹ nhàng", agent có thể giữ tone dịu hơn ở các lần sau.

`episodic memory` giúp agent nhớ bối cảnh các lần tâm sự trước. Ví dụ: user từng stress vì deadline, từng xung đột với bạn thân, hoặc từng chọn một bước hành động nhỏ. Loại memory này làm cuộc trò chuyện có cảm giác liên tục hơn, thay vì mỗi lần đều bắt đầu từ số không.

## 2. Memory nào rủi ro nhất?

Memory rủi ro nhất là `episodes.json`.

Lý do: episodic memory có thể chứa tóm tắt những chuyện rất riêng tư như sức khỏe tinh thần, xung đột gia đình, quan hệ cá nhân, áp lực công việc, hoặc cảm xúc tiêu cực. Nếu retrieve sai episode, agent có thể nhắc lại nhầm một chuyện nhạy cảm, làm user khó chịu hoặc cảm thấy bị xâm phạm.

`profile.json` cũng nhạy cảm nếu lưu các thông tin như tên thật, dị ứng, trigger cảm xúc, preference hỗ trợ, hoặc bất kỳ thông tin định danh nào. Với app tâm sự, cả profile và episodes đều cần được xem là dữ liệu cá nhân.

## 3. PII/privacy risks

Các rủi ro chính:

- Lưu PII không cần thiết, ví dụ tên thật, nơi làm việc, tên người thân, số điện thoại.
- Lưu nội dung tâm sự quá chi tiết trong `episodes.json`.
- Retrieve nhầm memory của user khác nếu sau này app có nhiều user nhưng chưa tách namespace.
- Agent nhắc lại memory nhạy cảm vào thời điểm không phù hợp.
- User không biết app đang lưu gì và không có cách xóa.

Trong version hiện tại, memory được lưu local trong thư mục `data/`, nên rủi ro network thấp hơn database remote. Tuy vậy, local JSON vẫn là dữ liệu nhạy cảm nếu máy bị chia sẻ hoặc repo bị upload nhầm.

## 4. Deletion, TTL, consent

Project hiện có lệnh CLI:

```text
/memory
/forget
```

`/memory` cho user xem tóm tắt memory hiện tại: profile, số episodes, số recent chat, số semantic notes.

`/forget` reset các file user memory:

```text
data/profile.json
data/episodes.json
data/chat_temp.json
```

`semantic_notes.json` không bị xóa bởi `/forget` vì đây là knowledge base chung của app, không phải memory cá nhân của user.

Nếu phát triển tiếp, nên thêm:

- Consent rõ ràng trước khi lưu memory dài hạn.
- TTL cho `chat_temp.json`, ví dụ tự xóa sau 24 giờ hoặc sau khi user exit.
- Tùy chọn "không lưu episode này" cho nội dung quá nhạy cảm.
- Namespace theo `user_id` nếu có nhiều user.
- Audit log tối thiểu để biết memory nào được tạo/cập nhật/xóa.

## 5. Conflict handling

Conflict quan trọng nhất trong lab là profile fact bị sửa. Ví dụ:

```text
User: Tôi dị ứng sữa bò.
User: À quên, tôi dị ứng đậu nành chứ không phải sữa bò.
Expected profile: allergy = đậu nành
```

Code hiện tại xử lý bằng cách ghi đè `profile["allergy"]` bằng fact mới, thay vì append thêm một allergy mâu thuẫn. Ngoài ra, các câu hỏi recall như "bữa trước tôi bị dị ứng gì đó nhỉ?" không được xem là fact mới, nên không ghi đè profile thành "gì đó nhỉ".

## 6. Technical limitations

Các hạn chế hiện tại:

- Semantic memory đang dùng keyword search fallback, chưa dùng Chroma/FAISS/vector embeddings. Vì vậy nếu user dùng từ đồng nghĩa xa, retrieval có thể miss.
- Profile extraction là rule-based, chỉ bắt một số pattern như tên, allergy, tone. Câu phức tạp hoặc mơ hồ có thể bị parse sai.
- Episodic memory đang lưu summary bằng cách lấy text user và outcome ngắn, chưa có LLM-based summarization/extraction riêng.
- Token budget đang trim theo số ký tự, chưa đếm token thật bằng tokenizer.
- Chưa có multi-user isolation. Nếu app phục vụ nhiều user, cần tách memory theo user/session.
- Chưa có safety classifier riêng cho self-harm/crisis; hiện mới dựa vào system prompt.
- Chưa có automated benchmark runner, benchmark đang là manual/evaluation table.

## 7. Khi nào system có thể fail khi scale?

System dễ fail khi:

- `episodes.json` quá dài, keyword search chậm và retrieve nhiều episode không liên quan.
- Nhiều user dùng chung một thư mục `data/`, gây lẫn memory.
- Fact conflict phức tạp hơn một field đơn giản, ví dụ nhiều allergy, allergy đã hết, hoặc allergy theo mức độ.
- User dùng cách nói vòng vo, sarcasm, hoặc phủ định phức tạp làm rule extractor hiểu sai.
- Local JSON bị ghi đồng thời bởi nhiều process.

Hướng nâng cấp:

- Dùng vector DB cho semantic/episodic retrieval.
- Thêm schema rõ hơn cho profile facts, có `source`, `confidence`, `created_at`, `updated_at`.
- Thêm LLM extraction với JSON schema và error handling.
- Dùng token counting thật.
- Thêm test tự động cho conflict update và memory deletion.

## 8. Kết luận

Memory làm agent tâm sự hữu ích hơn vì giúp giữ bối cảnh, nhớ preference và tránh bắt user kể lại từ đầu. Nhưng cùng lúc, memory trong app tâm sự là vùng dữ liệu nhạy cảm. Thiết kế tốt cần ưu tiên consent, deletion, TTL, hạn chế lưu PII, và tránh retrieve sai memory trong các tình huống riêng tư.
