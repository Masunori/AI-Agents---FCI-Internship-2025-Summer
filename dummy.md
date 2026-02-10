# Bản tin công nghệ - 30/01/2026

## Mở đầu



## Điểm nhấn: Mechanistic Data Attribution\: Tracing the Training Origins of Interpretable LLM Units

Framework Mechanistic Data Attribution (MDA) cho phép xác định chính xác các mẫu dữ liệu huấn luyện gây ra sự xuất hiện của các đơn vị LLM như induction heads. Thông qua Influence Functions mở rộng, MDA phát hiện rằng chỉ <10% mẫu có ảnh hưởng cao đủ để tăng tốc hoặc làm chậm quá trình hình thành circuit, trong khi can thiệp ngẫu nhiên không ảnh hưởng. Thí nghiệm trên bộ Pythia (14‑160M) chứng minh việc nhân đôi các mẫu này giảm thời gian hội tụ tới 30% và đồng thời nâng ICL Score lên 0.4‑0.5. Đối với FPT, công nghệ này mở đường cho việc điều chỉnh mô hình theo nhu cầu, giảm chi phí tiền luyện và tăng khả năng kiểm soát an toàn dữ liệu.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.21996v1

## Tin nhanh công nghệ

### News #1: Nvidia, Others in Talks for OpenAI Funding, Information Says \(2 minute read\)

OpenAI đang nhận đề nghị đầu tư từ Nvidia và các nhà đầu tư khác, nhằm mở rộng quy mô mô hình AI và tăng cường hạ tầng tính toán. Điều này cho thấy nhu cầu tài trợ quy mô lớn cho công nghệ AI, tạo cơ hội cho FPT khai thác các dịch vụ dựa trên OpenAI, nâng cao năng lực GPU và mở rộng giải pháp AI cho khách hàng.

**Ngày tổng hợp:** 30 Jan, 2026
**Nguồn:** TLDR News
**URL:** https://www.bloomberg.com/news/articles/2026-01-29/nvidia-others-in-talks-for-openai-investment-information-says?accessToken=%5B%27eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb3VyY2UiOiJTdWJzY3JpYmVyR2lmdGVkQXJ0aWNsZSIsImlhdCI6MTc2OTY2MzM5NSwiZXhwIjoxNzcwMjY4MTk1LCJhcnRpY2xlSWQiOiJUOUxWOVpUOU5KTTAwMCIsImJjb25uZWN0SWQiOiJBOEExRDhFQTI5OTc0OTRGQTQ1QUE2REJBMjAwNTM3MSJ9.CtVg11sPTmT3AptszWM12EBL1FNwxsvTZzythxxCYbo%27%5D&utm_source=%5B%27tldrai%27%5D

### News #2: TLDR is hiring a Senior Software Engineer, Applied AI \(\$200k\-\$300k, Fully Remote\)

TLDR tuyển Senior Software Engineer, Applied AI (lương $200‑300k, remote). Ứng viên sẽ xây dựng Claude Skills và AI agent tự động, tích hợp HubSpot, Google Drive, Slack, Sponsy, triển khai workflow trên n8n. Đây là bước quan trọng giúp TLDR tạo hệ thống AI‑native, giảm thời gian triển khai công cụ nội bộ, tăng năng suất cho các bộ phận không kỹ thuật – mô hình FPT có thể tham khảo để tự động hoá quy trình.

**Ngày tổng hợp:** 30 Jan, 2026
**Nguồn:** TLDR News
**URL:** https://jobs.ashbyhq.com/tldr.tech/3b21aaf8-dea5-4127-be71-602d30e5001e?utm_source=%5B%27tldrai%27%5D

### News #3: World Models \(15 minute read\)

World Models đang là trọng tâm toàn cầu: Yann LeCun thành lập lab chuyên, Google ra Genie 3, Meta công bố Code World Model 32B, đạt hoặc vượt mô hình lớn hơn trên SWE‑Bench, Terminal Bench. Đối với FPT, khả năng dự đoán trạng thái sau can thiệp (thị trường, chuỗi cung ứng, AI) giúp tối ưu chiến lược, giảm chi phí triển khai và tạo lợi thế cạnh tranh.

**Ngày tổng hợp:** 30 Jan, 2026
**Nguồn:** TLDR News
**URL:** https://ankitmaloo.com/world-models/?utm_source=%5B%27tldrai%27%5D

## Nghiên cứu khoa học nổi bật

### Article #1: SINA\: A Circuit Schematic Image\-to\-Netlist Generator Using Artificial Intelligence

Đã ra mắt SINA – công cụ AI tự động chuyển ảnh sơ đồ mạch sang netlist SPICE, kết hợp YOLOv11, CCL, OCR và mô hình ngôn ngữ thị giác. Độ chính xác tạo netlist đạt 96,47%, cao gấp 2,72 × so với giải pháp hiện tại. Với FPT, SINA giảm thời gian và lỗi khi nhập dữ liệu mạch, hỗ trợ xây dựng bộ dữ liệu lớn cho AI EDA và tăng năng suất thiết kế.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.22114v1

### Article #2: Unsupervised Decomposition and Recombination with Discriminator\-Driven Diffusion Models

Phương pháp mới tích hợp **bộ phân biệt (discriminator) vào mô hình khuế tán (diffusion)** giúp mô hình tự động tách và tái hợp các thành phần dữ liệu mà không cần giám sát nhãn. Nhờ tín hiệu đối kháng, FID giảm đáng kể trên CelebA‑HQ, VKITTI, CLEVR và Falcor3D; trên Falcor3D **MIG** và **MCC** tăng lên, chứng tỏ khả năng tách yếu tố tốt hơn. Đối với robot, phạm vi khám phá trạng thái tăng **35.8 %** (Scene 5) và **73.8 %** (Scene 6), mở ra tiềm năng nâng cao hiệu suất tự động hoá và dịch vụ đám mây của FPT.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.22057v1

### Article #3: Liquid Interfaces\: A Dynamic Ontology for the Interoperability of Autonomous Systems

Liquid Interfaces thay đổi cách tích hợp hệ thống: giao diện không còn là hợp đồng tĩnh mà là sự kiện quan hệ ngắn hạn, được tạo ra qua biểu đạt ý định và đàm phán ngữ nghĩa tại thời gian chạy. Điều này giúp FPT giảm chi phí bảo trì – loại bỏ nợ kỹ thuật cố định – và tăng khả năng phối hợp nhanh chóng giữa agent AI, đáp ứng môi trường kinh doanh biến đổi.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.21993v1

### Article #4: Exploring Reasoning Reward Model for Agents

Giới thiệu Agent‑RRM – mô hình thưởng đa chiều cung cấp dấu vết suy luận, chỉ trích chi tiết và điểm tổng hợp cho các hành trình của agent. Ba cách tích hợp (Reagent‑C, Reagent‑R, Reagent‑U) cho phép tinh chỉnh bằng ngôn ngữ, bổ sung phần thưởng và hợp nhất phản hồi. Reagent‑U đạt 43.7 % trên GAIA và 46.2 % trên WebWalkerQA, vượt trội so với phương pháp hiện có, hứa hẹn nâng cao năng lực AI công cụ của FPT.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.22154v1

### Article #5: Geometry of Drifting MDPs with Path\-Integral Stability Certificates

Phát triển khung hình học cho MDP thay đổi theo đường đồng nhất, định lượng ba thành phần : độ dài (cumulative drift), độ cong (tăng tốc/dao động) và “kink” (gần‑tie hành động). Dựa trên bound ổn định dạng path‑integral, nhóm đề xuất hai wrapper HT‑RL và HT‑MCTS, tự động ước lượng các chỉ báo này và điều chỉnh tốc độ học, tần suất cập nhật mục tiêu và ngân sách tìm kiếm. Kết quả thực nghiệm cho thấy cải thiện đáng kể khả năng theo dõi môi trường phi‑tĩnh và giảm regret động so với các baseline tĩnh.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.21991v1

### Article #6: Mind the Gap\: How Elicitation Protocols Shape the Stated\-Revealed Preference Gap in Language Models

Cho phép mô hình biểu đạt trung lập khi khai báo sở thích (stated) nâng hệ số tương quan SvR lên ρ≈0.7; cho phép trung lập ở mức hành vi (revealed) làm ρ giảm gần 0 hoặc âm. Prompt hệ thống dựa trên thứ tự giá trị tự khai báo không cải thiện, thậm chí giảm hiệu suất. Vì vậy FPT cần thiết kế giao thức thu thập sở thích tính đến sự không chắc chắn, tránh câu hỏi nhị phân.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.21975v1

### Article #7: How do Visual Attributes Influence Web Agents? A Comprehensive Evaluation of User Interface Design Factors

Ra mắt VAF – quy trình đánh giá ảnh hưởng của thuộc tính giao diện lên quyết định của web‑agent. VAF tạo 8 họ biến thể, 48 phiên bản trên 5 trang web, kiểm thử 4 agent, cho thấy màu nền tương phản, kích thước và vị trí tăng TCR tới 11,7 % và 20 % so với gốc; phông chữ, màu chữ, độ nét ảnh ít ảnh hưởng. Điều này giúp FPT tối ưu UI cho AI, nâng cao tin cậy.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.21961v1

### Article #8: DynaWeb\: Model\-Based Reinforcement Learning of Web Agents

DynaWeb giới thiệu mô hình RL dựa trên thế giới ảo cho web agent, cho phép đào tạo bằng “giấc mơ” thay vì tương tác thực tế, giảm chi phí. Trên WebArena, thành công tăng từ 26.7 % lên 31.0 % (+16.1 %); trên WebVoyager đạt kết quả tốt nhất. Kết hợp 40 % dữ liệu thực với rollouts mô phỏng giúp ổn định học và giảm nhu cầu truy cập internet, phù hợp với chiến lược tăng năng suất và bảo mật của FPT.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.22149v1

### Article #9: Investigating Associational Biases in Inter\-Model Communication of Large Generative Models

Trong pipeline giao tiếp mô‑hình sinh ảnh‑mô tả, phân phối nhân khẩu học dịch chuyển: độ tuổi trẻ hơn tăng từ 33,05 % lên 85,78 %; tỷ lệ người nữ tăng từ 22,80 % lên 66,24 % (âm nhạc/dance) và từ 59,14 % lên 91,96 % (hạnh phúc). Điều này cho thấy mô hình khuếch đại định kiến giới và tuổi, ảnh hưởng tới công bằng AI của FPT, cần kiểm soát bias ngay trong thiết kế.

**Ngày xuất bản:** 29 Jan, 2026
**Nguồn:** arXiV cs.AI
**URL:** https://arxiv.org/pdf/2601.22093v1

## Kết luận



| Tiêu đề | Ngày xuất bản | URL |
|---|---|---|
| Mechanistic Data Attribution\: Tracing the Training Origins of Interpretable LLM Units | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.21996v1) |
| Nvidia, Others in Talks for OpenAI Funding, Information Says \(2 minute read\) | 30 Jan, 2026 | [Link](https://www.bloomberg.com/news/articles/2026-01-29/nvidia-others-in-talks-for-openai-investment-information-says?accessToken=%5B%27eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb3VyY2UiOiJTdWJzY3JpYmVyR2lmdGVkQXJ0aWNsZSIsImlhdCI6MTc2OTY2MzM5NSwiZXhwIjoxNzcwMjY4MTk1LCJhcnRpY2xlSWQiOiJUOUxWOVpUOU5KTTAwMCIsImJjb25uZWN0SWQiOiJBOEExRDhFQTI5OTc0OTRGQTQ1QUE2REJBMjAwNTM3MSJ9.CtVg11sPTmT3AptszWM12EBL1FNwxsvTZzythxxCYbo%27%5D&utm_source=%5B%27tldrai%27%5D) |
| TLDR is hiring a Senior Software Engineer, Applied AI \(\$200k\-\$300k, Fully Remote\) | 30 Jan, 2026 | [Link](https://jobs.ashbyhq.com/tldr.tech/3b21aaf8-dea5-4127-be71-602d30e5001e?utm_source=%5B%27tldrai%27%5D) |
| World Models \(15 minute read\) | 30 Jan, 2026 | [Link](https://ankitmaloo.com/world-models/?utm_source=%5B%27tldrai%27%5D) |
| SINA\: A Circuit Schematic Image\-to\-Netlist Generator Using Artificial Intelligence | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.22114v1) |
| Unsupervised Decomposition and Recombination with Discriminator\-Driven Diffusion Models | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.22057v1) |
| Liquid Interfaces\: A Dynamic Ontology for the Interoperability of Autonomous Systems | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.21993v1) |
| Exploring Reasoning Reward Model for Agents | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.22154v1) |
| Geometry of Drifting MDPs with Path\-Integral Stability Certificates | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.21991v1) |
| Mind the Gap\: How Elicitation Protocols Shape the Stated\-Revealed Preference Gap in Language Models | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.21975v1) |
| How do Visual Attributes Influence Web Agents? A Comprehensive Evaluation of User Interface Design Factors | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.21961v1) |
| DynaWeb\: Model\-Based Reinforcement Learning of Web Agents | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.22149v1) |
| Investigating Associational Biases in Inter\-Model Communication of Large Generative Models | 29 Jan, 2026 | [Link](https://arxiv.org/pdf/2601.22093v1) |

---
Bản tin được tạo tự động bởi hệ thống FCI News Agents.