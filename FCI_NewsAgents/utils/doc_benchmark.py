from typing import List

from FCI_NewsAgents.models.document import Document

IRRELEVANT_DOCS = [
    Document(
        url="https://arxiv.org/abs/2512.16919",
        title="DVGT: Driving Visual Geometry Transformer",
        summary="Perceiving and reconstructing 3D scene geometry from visual inputs is crucial for autonomous driving. However, there still lacks a driving-targeted dense geometry perception model that can adapt to different scenarios and camera configurations. To bridge this gap, we propose a Driving Visual Geometry Transformer (DVGT), which reconstructs a global dense 3D point map from a sequence of unposed multi-view visual inputs. We first extract visual features for each image using a DINO backbone, and employ alternating intra-view local attention, cross-view spatial attention, and cross-frame temporal attention to infer geometric relations across images. We then use multiple heads to decode a global point map in the ego coordinate of the first frame and the ego poses for each frame. Unlike conventional methods that rely on precise camera parameters, DVGT is free of explicit 3D geometric priors, enabling flexible processing of arbitrary camera configurations. DVGT directly predicts metric-scaled geometry from image sequences, eliminating the need for post-alignment with external sensors. Trained on a large mixture of driving datasets including nuScenes, OpenScene, Waymo, KITTI, and DDAD, DVGT significantly outperforms existing models on various scenarios. Code is available at this https URL.",
        source="arXiv",
        authors=["Sicheng Zuo", "Zixun Xie", "Wenzhao Zheng", "Shaoqing Xu", "Fang Li", "Shengyin Jiang", "Long Chen", "Zhi-Xin Yang", "Jiwen Lu"],
        published_date="2025-12-18",
        content_type="paper"
    ),
    Document(
        url="https://arxiv.org/abs/2512.15767",
        title="Bridging Data and Physics: A Graph Neural Network-Based Hybrid Twin Framework",
        summary="Simulating complex unsteady physical phenomena relies on detailed mathematical models, simulated for instance by using the Finite Element Method (FEM). However, these models often exhibit discrepancies from the reality due to unmodeled effects or simplifying assumptions. We refer to this gap as the ignorance model. While purely data-driven approaches attempt to learn full system behavior, they require large amounts of high-quality data across the entire spatial and temporal domain. In real-world scenarios, such information is unavailable, making full data-driven modeling unreliable. To overcome this limitation, we model of the ignorance component using a hybrid twin approach, instead of simulating phenomena from scratch. Since physics-based models approximate the overall behavior of the phenomena, the remaining ignorance is typically lower in complexity than the full physical response, therefore, it can be learned with significantly fewer data. A key difficulty, however, is that spatial measurements are sparse, also obtaining data measuring the same phenomenon for different spatial configurations is challenging in practice. Our contribution is to overcome this limitation by using Graph Neural Networks (GNNs) to represent the ignorance model. GNNs learn the spatial pattern of the missing physics even when the number of measurement locations is limited. This allows us to enrich the physics-based model with data-driven corrections without requiring dense spatial, temporal and parametric data. To showcase the performance of the proposed method, we evaluate this GNN-based hybrid twin on nonlinear heat transfer problems across different meshes, geometries, and load positions. Results show that the GNN successfully captures the ignorance and generalizes corrections across spatial configurations, improving simulation accuracy and interpretability, while minimizing data requirements.",
        source="arXiv",
        authors=["M. Gorpinich (1 and 2)", "B. Moya (2)", "S. Rodriguez (2)", "F. Meraghni (2)", "Y. Jaafra (1)", "A. Briot (1)", "M. Henner (1)", "R. Leon (1)", "F. Chinesta (2 and 3) ((1) Valeo, (2) PIMM Lab. ENSAM Institute of Technology, (3) CNRS@CREATE LTD. Singapore)"],
        published_date="2025-12-12",
        content_type="paper"
    ),
    Document(
        url="https://www.wsj.com/tech/ai/openai-ends-vesting-cliff-for-new-employees-in-compensation-policy-change-d4c4c2cd",
        title="OpenAI Ends Vesting Cliff for New Employees in Compensation Policy Change",
        summary="OpenAI has ended a compensation policy that required employees to work at the company for at least six months before their equity vests. The change is designed to encourage new employees to take risks without fear of being let go before accessing their first chunk of equity. OpenAI had shortened its vesting period for new employees to six months from the industry standard of 12 months in April. xAI also made a similar change in the late summer.",
        source="The Wall Street Journal",
        authors=["Meghan Bobrowsky", "Berber Jin", "Georgia Wells"],
        published_date="2024-12-13",
        content_type="article"
    ),
    Document(
        url="https://openai.com/index/chatgpt-shopping-research/",
        title="Introducing shopping research in ChatGPT",
        summary="A new shopping experience that helps you find the right products for you.",
        source="OpenAI",
        authors=["The ChatGPT Team"],
        published_date="2024-11-25",
        content_type="article"
    ),
    Document(
        url="https://news.mit.edu/2025/3-questions-yunha-hwang-using-computation-study-worlds-best-single-celled-chemists-1215",
        title="3 Questions: Using computation to study the world’s best single-celled chemists",
        summary="Assistant Professor Yunha Hwang utilizes microbial genomes to examine the language of biology. Her appointment reflects MIT’s commitment to exploring the intersection of genetics research and AI.",
        source="MIT News",
        authors=["Lillian Eden"],
        published_date="2025-12-15",
        content_type="article"
    ),
    Document(
        url="https://techcrunch.com/2025/12/12/data-breach-at-credit-check-giant-700credit-affects-at-least-5-6-million/",
        title="Data breach at credit check giant 700Credit affects at least 5.6 million",
        summary="A hacker accessed 700Credit's systems and stole personal data, including names, addresses, dates of birth, and Social Security numbers for at least 5.6 million people whose details were collected by US auto dealerships between May and October. The company is notifying victims by mail. Michigan's attorney general has urged affected individuals to use credit freezes or monitoring to reduce their risk of fraud.",
        source="TechCrunch",
        authors=["Zack Whittaker"],
        published_date="2025-12-12",
        content_type="article"
    ),
    Document(
        url="https://clickhouse.com/blog/parallelizing-fixed-hashmap-aggregation-merge-in-clickhouse",
        title="Parallelizing Fixed HashMap Aggregation Merge in ClickHouse",
        summary="ClickHouse 25.11 introduces parallel merge for small GROUP BY operations, harnessing multithreading to accelerate aggregations on 8-bit and 16-bit keys by partitioning FixedHashMap-based merge phases among threads. Performance gains are significant for complex aggregations, but overhead limits benefits for trivial operations, so the optimization is disabled in those cases. This enhancement directly boosts query efficiency for data processing workflows involving high-cardinality small-key groupings.",
        source="ClickHouse Blog",
        authors=["Jianfei Hu"],
        published_date="2025-12-16",
        content_type="article"
    ),
    Document(
        url="https://www.dataprojecthunt.com/",
        title="Data Project Hunt",
        summary="Data Project Hunt is a community site for discovering and showcasing data engineering projects, built around weekly “launches,” voting, and maker recognition. It lets you submit projects, browse curated listings, filter by stack, follow recent activity, and see leaderboards for both projects and makers. A place to learn from real-world best practices and share your innovations.",
        source="Data Project Hunt",
        authors=[],
        published_date="2024-06-01",
        content_type="article"
    ),
    Document(
        url="https://news.mit.edu/2025/deep-learning-model-predicts-how-fruit-flies-form-1215",
        title="Deep learning model predicts how fruit flies form memories, cell by cell",
        summary="The approach could apply to more complex tissues and organs, helping researchers to identify early signs of disease.",
        source="MIT News",
        authors=["Jennifer Chu"],
        published_date="2025-12-15",
        content_type="article"
    ),
    Document(
        url="https://techcrunch.com/2025/12/23/hackers-stole-over-2-7-billion-in-crypto-in-2025-data-shows/",
        title="Hackers stole over $2.7 billion in crypto in 2025, data shows",
        summary="Cybercriminals stole $2.7 billion in crypto this year, a new record for crypto-stealing hacks, according to blockchain-monitoring firms. Once again, in 2025, there were dozens of crypto heists hitting several cryptocurrency exchanges and other web3 and decentralized finance (DeFi) projects. The biggest hack by far was the breach at Dubai-based crypto exchange Bybit, where hackers stole around $1.4 billion in crypto. Blockchain analysis firms, as well as the FBI, accused North Korean government hackers — the most prolific group targeting crypto in the last few years — of this massive heist.",
        source="TechCrunch",
        authors=["Lorenzo Franceschi-Bicchierai"],
        published_date="2025-12-23",
        content_type="article"
    ),
    Document(
        url="https://arxiv.org/abs/2512.09487",
        title="RouteRAG: Efficient Retrieval-Augmented Generation from Text and Graph via Reinforcement Learning",
        summary="Retrieval-Augmented Generation (RAG) integrates non-parametric knowledge into Large Language Models (LLMs), typically from unstructured texts and structured graphs. While recent progress has advanced text-based RAG to multi-turn reasoning through Reinforcement Learning (RL), extending these advances to hybrid retrieval introduces additional challenges. Existing graph-based or hybrid systems typically depend on fixed or handcrafted retrieval pipelines, lacking the ability to integrate supplementary evidence as reasoning unfolds. Besides, while graph evidence provides relational structures crucial for multi-hop reasoning, it is substantially more expensive to retrieve. To address these limitations, we introduce RouteRAG, an RL-based framework that enables LLMs to perform multi-turn and adaptive graph-text hybrid RAG. RouteRAG jointly optimizes the entire generation process via RL, allowing the model to learn when to reason, what to retrieve from either texts or graphs, and when to produce final answers, all within a unified generation policy. To guide this learning process, we design a two-stage training framework that accounts for both task outcome and retrieval efficiency, enabling the model to exploit hybrid evidence while avoiding unnecessary retrieval overhead. Experimental results across five question answering benchmarks demonstrate that RouteRAG significantly outperforms existing RAG baselines, highlighting the benefits of end-to-end RL in supporting adaptive and efficient retrieval for complex reasoning.",
        source="arXiv",
        authors=["Yucan Guo", "Miao Su", "Saiping Guan", "Zihao Sun", "Xiaolong Jin", "Jiafeng Guo", "Xueqi Cheng"],
        published_date="2025-12-18",
        content_type="paper"
    )
]

RELEVANT_DOCS_CLOUD = [
    Document(
        url="https://www.aboutamazon.com/news/aws/graviton4-aws-cloud-computing-chip",
        title="Amazon's new cloud computing chip, AWS Graviton4, is now generally available. Take a look back at its evolution.",
        summary="Launched in 2018, the custom AWS-engineered data center chip was the first of its kind to be deployed at scale by a major cloud provider. Graviton brought the same efficiency to AWS data centers, and all the power required by AWS customers. How powerful? Graviton4 offers four times the performance of Graviton1. How efficient? Graviton3 uses 60 percent less energy for the same performance as comparable Amazon EC2 instances (where the compute happens in a data center), and Graviton4 is even more energy efficient. How many transistors are in the chip? Glad you asked: 73 billion transistors, which in compute terms is the equivalent of a whole, whole, lot.",
        source="About Amazon",
        authors=["Amazon Staff"],
        published_date="2024-07-09",
        content_type="article"
    ),
    Document(
        url="https://blog.cloudflare.com/workers-ai/",
        title="Workers AI: serverless GPU-powered inference on Cloudflare’s global network",
        summary="We’re launching Workers AI to put AI inference in the hands of every developer, and to actually deliver on that goal, it should just work out of the box. How do we achieve that? At the core of everything, it runs on the right infrastructure - our world-class network of GPUs. We provide off-the-shelf models that run seamlessly on our infrastructure. Finally, deliver it to the end developer, in a way that’s delightful. A developer should be able to build their first Workers AI app in minutes, and say “Wow, that’s kinda magical!”. So what exactly is Workers AI? It’s another building block that we’re adding to our developer platform - one that helps developers run well-known AI models on serverless GPUs, all on Cloudflare’s trusted global network. As one of the latest additions to our developer platform, it works seamlessly with Workers + Pages, but to make it truly accessible, we’ve made it platform-agnostic, so it also works everywhere else, made available via a REST API.",
        source="Cloudflare Blog",
        authors=["Phil Wittig", "Rita Kozlov", "Rebecca Weekly", "Celso Martinho", "Meaghan Choi"],
        published_date="2023-09-27",
        content_type="article"
    ),
    Document(
        url="https://journalwjarr.com/sites/default/files/fulltext_pdf/WJARR-2025-1538.pdf",
        title="Optimizing low latency public cloud systems: Strategies for network, compute and storage efficiency",
        summary="Your public cloud environment can't run at low latency in today's digital-driven landscape, so it has become a strategic necessity. This comprehensive article discusses actionable strategies for latency optimization in public cloud systems traversing across network, compute, and storage layers. Though slower than form 2, form 3 cannot be recommended for imports because it presents challenges like How to easily make duplex payments with very high values. Reading form 4, you will learn how a decentralized finance system comprises different core components. This delves deep into the root causes of latency, like Geographic distance, resource contention, and inefficient configurations, and proffers sufficient guidance on combatting these through architectural best practices, edge computing, private connectivity, and intelligent resource selection. It also explores how real-time monitoring, predictive benchmarking, and automation tools allow organizations to detect and deal with latency problems before those affect the user experience. New technologies like AI/ML and 5G are targeted as these technologies will completely transform cloud performance optimization through the ability to make proactive decisions and super-fast connectivity. Besides, real-world case studies show successful implementations and cautionary failures and give useful lessons for IT leaders and cloud architects. This guide offers readers the tools and knowledge to build fast, scalable, and reliable cloud applications in both a single—or, indeed, a multi—or, not least, hybrid environment. The aim is easy: their clouds should not only work but work in an optimized way for all those milliseconds of performance and response time.",
        source="World Journal of Advanced Research and Reviews",
        authors=["Piyush Patil"],
        published_date="2025-05-01",
        content_type="paper"
    ),
    Document(
        url="https://aws.amazon.com/blogs/aws/introducing-amazon-nova-forge-build-your-own-frontier-models-using-nova/",
        title="Introducing Amazon Nova Forge: Build Your Own Frontier Models Using Nova",
        summary="Today, we’re introducing Amazon Nova Forge, a new service to build your own frontier models using Nova. Nova Forge customers can start their development from early model checkpoints, blend their datasets with Amazon Nova-curated training data, and host their custom models securely on AWS. Nova Forge is the easiest and most cost-effective way to build your own frontier model.",
        source="AWS News Blog",
        authors=["Danilo Poccia"],
        published_date="2025-12-02",
        content_type="article"
    )
]

RELEVANT_DOCS_SYSTEMS = [
    Document(
        url="https://developer.nvidia.com/blog/boost-gpu-memory-performance-with-no-code-changes-using-nvidia-cuda-mps/",
        title="Boost GPU Memory Performance with No-Code Changes Using NVIDIA CUDA MPS",
        summary="NVIDIA MLOPart is a new CUDA MPS feature for Blackwell GPUs that lets a single GPU be split into multiple low-latency CUDA devices with dedicated compute and memory, enabling transparent A/B testing of latency-sensitive workloads without code changes. MLOPart devices retain the same compute capability, PCI IDs, and P2P support as the parent GPU, but expose fewer SMs and partitioned memory (with shared virtual address space and weaker isolation). They’re identified by UUIDs for fine-grained selection via CUDA_VISIBLE_DEVICES. Compared to MIG, MLOPart does not provide strict isolation, requires no root access, and is configured per user/server. It typically improves memory latency and intra-GPU P2P bandwidth, at the cost of reduced DRAM bandwidth and per-device compute. Currently supported on x86 only.",
        source="NVIDIA Developer Blog",
        authors=["Sherwin Nassernia"],
        published_date="2025-12-16",
        content_type="article"
    ),
    Document(
        url="https://developer.nvidia.com/blog/aws-integrates-ai-infrastructure-with-nvidia-nvlink-fusion-for-trainium4-deployment/",
        title="AWS Integrates AI Infrastructure with NVIDIA NVLink Fusion for Trainium4 Deployment",
        summary="Amazon Web Services and NVIDIA announced a collaboration at AWS re:Invent to integrate NVIDIA NVLink Fusion, allowing for faster deployment of custom AI infrastructure, including for the new Trainium4 AI chips and Graviton CPUs. NVLink Fusion provides a scalable, high-bandwidth networking solution that connects up to 72 custom ASICs with NVIDIA's sixth generation NVLink Switch, enabling improved performance and easier management of increasingly complex AI workloads. By using NVIDIA's modular technology stack and extensive ecosystem, hyperscalers like AWS can reduce development costs, lower deployment risks, and speed up time to market for custom AI silicon and infrastructure.",
        source="NVIDIA Developer Blog",
        authors=["Jesse Clayton"],
        published_date="2025-12-02",
        content_type="article"
    )
]

RELEVANT_DOCS_AI = [
    Document(
        url="https://news.mit.edu/2025/enabling-small-language-models-solve-complex-reasoning-tasks-1212",
        title="Enabling small language models to solve complex reasoning tasks",
        summary="The “self-steering” DisCIPL system directs small models to work together on tasks with constraints, like itinerary planning and budgeting.",
        source="MIT News",
        authors=["Alex Shipps"],
        published_date="2025-12-12",
        content_type="article"
    ),
    Document(
        url="https://developer.nvidia.com/blog/accelerating-long-context-inference-with-skip-softmax-in-nvidia-tensorrt-llm/",
        title="Accelerating Long-Context Inference with Skip Softmax in NVIDIA TensorRT LLM",
        summary="NVIDIA’s TensorRT-LLM adds a new Skip Softmax optimization to the FlashAttention kernel for long-context LLM inference. It works by dynamically detecting and skipping attention blocks whose contributions would be negligible (based on comparing local max logits to a running global max with a threshold), so the GPU avoids unnecessary softmax computation, value-block loads, and matrix multiplications. This reduces both memory bandwidth use and compute cost during inference without retraining the model. Benchmarks on models like Llama 3.3-70B and Qwen-8B show up to ~1.4× speedup in both prefill and decode phases with near-lossless accuracy at ~50% sparsity. Skip Softmax is supported on NVIDIA Hopper and Blackwell GPUs and can be enabled/configured via TensorRT-LLM’s API or YAML options.",
        source="NVIDIA Developer Blog",
        authors=["Laikh Tewari", "Kai Xu", "Bo Li", "Fred Oh"],
        published_date="2025-12-16",
        content_type="article"
    ),
    Document(
        url="https://openai.com/index/introducing-gpt-5-2-codex/",
        title="Introducing GPT-5.2 Codex",
        summary="The most advanced agentic coding model for professional software engineering and defensive cybersecurity.",
        source="OpenAI",
        authors=["The OpenAI Team"],
        published_date="2025-12-18",
        content_type="article"
    ),
    Document(
        url="https://arxiv.org/abs/2502.18139",
        title="LevelRAG: Enhancing Retrieval-Augmented Generation with Multi-hop Logic Planning over Rewriting Augmented Searchers",
        summary="Retrieval-Augmented Generation (RAG) is a crucial method for mitigating hallucinations in Large Language Models (LLMs) and integrating external knowledge into their responses. Existing RAG methods typically employ query rewriting to clarify the user intent and manage multi-hop logic, while using hybrid retrieval to expand search scope. However, the tight coupling of query rewriting to the dense retriever limits its compatibility with hybrid retrieval, impeding further RAG performance improvements. To address this challenge, we introduce a high-level searcher that decomposes complex queries into atomic queries, independent of any retriever-specific optimizations. Additionally, to harness the strengths of sparse retrievers for precise keyword retrieval, we have developed a new sparse searcher that employs Lucene syntax to enhance retrieval this http URL web and dense searchers, these components seamlessly collaborate within our proposed method, \textbf{LevelRAG}. In LevelRAG, the high-level searcher orchestrates the retrieval logic, while the low-level searchers (sparse, web, and dense) refine the queries for optimal retrieval. This approach enhances both the completeness and accuracy of the retrieval process, overcoming challenges associated with current query rewriting techniques in hybrid retrieval scenarios. Empirical experiments conducted on five datasets, encompassing both single-hop and multi-hop question answering tasks, demonstrate the superior performance of LevelRAG compared to existing RAG methods. Notably, LevelRAG outperforms the state-of-the-art proprietary model, GPT4o, underscoring its effectiveness and potential impact on the RAG field.",
        source="arXiv",
        authors=["Zhuocheng Zhang", "Yang Feng", "Min Zhang"],
        published_date="2025-02-25",
        content_type="paper"
    ),
    Document(
        url="https://arxiv.org/abs/2512.03262",
        title="Is Vibe Coding Safe? Benchmarking Vulnerability of Agent-Generated Code in Real-World Tasks",
        summary="Vibe coding is a new programming paradigm in which human engineers instruct large language model (LLM) agents to complete complex coding tasks with little supervision. Although it is increasingly adopted, are vibe coding outputs really safe to deploy in production? To answer this question, we propose SU S VI B E S, a benchmark consisting of 200 feature-request software engineering tasks from real-world open-source projects, which, when given to human programmers, led to vulnerable implementations. We evaluate multiple widely used coding agents with frontier models on this benchmark. Disturbingly, all agents perform poorly in terms of software security. Although 61% of the solutions from SWE-Agent with Claude 4 Sonnet are functionally correct, only 10.5% are secure. Further experiments demonstrate that preliminary security strategies, such as augmenting the feature request with vulnerability hints, cannot mitigate these security issues. Our findings raise serious concerns about the widespread adoption of vibe-coding, particularly in security-sensitive applications.",
        source="arXiv",
        authors=["Songwen Zhao", "Danqing Wang", "Kexun Zhang", "Jiaxuan Luo", "Zhuo Li", "Lei Li"],
        published_date="2025-12-02",
        content_type="paper"
    ),
    Document(
        url="https://aws.amazon.com/blogs/aws/introducing-amazon-nova-forge-build-your-own-frontier-models-using-nova/",
        title="Introducing Amazon Nova Forge: Build Your Own Frontier Models Using Nova",
        summary="Today, we’re introducing Amazon Nova Forge, a new service to build your own frontier models using Nova. Nova Forge customers can start their development from early model checkpoints, blend their datasets with Amazon Nova-curated training data, and host their custom models securely on AWS. Nova Forge is the easiest and most cost-effective way to build your own frontier model.",
        source="AWS News Blog",
        authors=["Danilo Poccia"],
        published_date="2025-12-02",
        content_type="article"
    ),
    Document(
        url="https://arxiv.org/abs/2512.04123",
        title="Measuring Agents in Production",
        summary="AI agents are actively running in production across diverse industries, yet little is publicly known about which technical approaches enable successful real-world deployments. We present the first large-scale systematic study of AI agents in production, surveying 306 practitioners and conducting 20 in-depth case studies via interviews across 26 domains. We investigate why organizations build agents, how they build them, how they evaluate them, and what the top development challenges are. We find that production agents are typically built using simple, controllable approaches: 68% execute at most 10 steps before requiring human intervention, 70% rely on prompting off-the-shelf models instead of weight tuning, and 74% depend primarily on human evaluation. Reliability remains the top development challenge, driven by difficulties in ensuring and evaluating agent correctness. Despite these challenges, simple yet effective methods already enable agents to deliver impact across diverse industries. Our study documents the current state of practice and bridges the gap between research and deployment by providing researchers visibility into production challenges while offering practitioners proven patterns from successful deployments.",
        source="arXiv",
        authors=["Melissa Z. Pan", "Negar Arabzadeh", "Riccardo Cogo", "Yuxuan Zhu", "Alexander Xiong", "Lakshya A Agrawal", "Huanzhi Mao", "Emma Shen", "Sid Pallerla", "Liana Patel", "Shu Liu", "Tianneng Shi", "Xiaoyuan Liu", "Jared Quincy Davis", "Emmanuele Lacavalla", "Alessandro Basile", "Shuyi Yang", "Paul Castro", "Daniel Kang", "Joseph E. Gonzalez", "Koushik Sen", "Dawn Song", "Ion Stoica", "Matei Zaharia", "Marquita Ellis"],
        published_date="2025-12-02",
        content_type="paper"
    ),
    Document(
        url="https://arxiv.org/abs/2512.02556",
        title="DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models",
        summary="We introduce DeepSeek-V3.2, a model that harmonizes high computational efficiency with superior reasoning and agent performance. The key technical breakthroughs of DeepSeek-V3.2 are as follows: (1) DeepSeek Sparse Attention (DSA): We introduce DSA, an efficient attention mechanism that substantially reduces computational complexity while preserving model performance in long-context scenarios. (2) Scalable Reinforcement Learning Framework: By implementing a robust reinforcement learning protocol and scaling post-training compute, DeepSeek-V3.2 performs comparably to GPT-5. Notably, our high-compute variant, DeepSeek-V3.2-Speciale, surpasses GPT-5 and exhibits reasoning proficiency on par with Gemini-3.0-Pro, achieving gold-medal performance in both the 2025 International Mathematical Olympiad (IMO) and the International Olympiad in Informatics (IOI). (3) Large-Scale Agentic Task Synthesis Pipeline: To integrate reasoning into tool-use scenarios, we developed a novel synthesis pipeline that systematically generates training data at scale. This methodology facilitates scalable agentic post-training, yielding substantial improvements in generalization and instruction-following robustness within complex, interactive environments.",
        source="arXiv",
        authors = [
            "Aixin Liu", "Aoxue Mei", "Bangcai Lin", "Bing Xue", "Bingxuan Wang",
            "Bingzheng Xu", "Bochao Wu", "Bowei Zhang", "Chaofan Lin", "Chen Dong",
            "Chengda Lu", "Chenggang Zhao", "Chengqi Deng", "Chenhao Xu", "Chong Ruan",
            "Damai Dai", "Daya Guo", "Dejian Yang", "Deli Chen", "Erhang Li",
            "Fangqi Zhou", "Fangyun Lin", "Fucong Dai", "Guangbo Hao", "Guanting Chen",
            "Guowei Li", "H. Zhang", "Hanwei Xu", "Hao Li", "Haofen Liang",
            "Haoran Wei", "Haowei Zhang", "Haowen Luo", "Haozhe Ji", "Honghui Ding",
            "Hongxuan Tang", "Huanqi Cao", "Huazuo Gao", "Hui Qu", "Hui Zeng",
            "Jialiang Huang", "Jiashi Li", "Jiaxin Xu", "Jiewen Hu", "Jingchang Chen",
            "Jingting Xiang", "Jingyang Yuan", "Jingyuan Cheng", "Jinhua Zhu", "Jun Ran",
            "Junguang Jiang", "Junjie Qiu", "Junlong Li", "Junxiao Song", "Kai Dong",
            "Kaige Gao", "Kang Guan", "Kexin Huang", "Kexing Zhou", "Kezhao Huang",
            "Kuai Yu", "Lean Wang", "Lecong Zhang", "Lei Wang", "Liang Zhao",
            "Liangsheng Yin", "Lihua Guo", "Lingxiao Luo", "Linwang Ma", "Litong Wang",
            "Liyue Zhang", "M.S. Di", "M.Y Xu", "Mingchuan Zhang", "Minghua Zhang",
            "Minghui Tang", "Mingxu Zhou", "Panpan Huang", "Peixin Cong", "Peiyi Wang",
            "Qiancheng Wang", "Qihao Zhu", "Qingyang Li", "Qinyu Chen", "Qiushi Du",
            "Ruiling Xu", "Ruiqi Ge", "Ruisong Zhang", "Ruizhe Pan", "Runji Wang",
            "Runqiu Yin", "Runxin Xu", "Ruomeng Shen", "Ruoyu Zhang", "S.H. Liu",
            "Shanghao Lu", "Shangyan Zhou", "Shanhuang Chen", "Shaofei Cai", "Shaoyuan Chen",
            "Shengding Hu", "Shengyu Liu", "Shiqiang Hu", "Shirong Ma", "Shiyu Wang",
            "Shuiping Yu", "Shunfeng Zhou", "Shuting Pan", "Songyang Zhou", "Tao Ni",
            "Tao Yun", "Tian Pei", "Tian Ye", "Tianyuan Yue", "Wangding Zeng",
            "Wen Liu", "Wenfeng Liang", "Wenjie Pang", "Wenjing Luo", "Wenjun Gao",
            "Wentao Zhang", "Xi Gao", "Xiangwen Wang", "Xiao Bi", "Xiaodong Liu",
            "Xiaohan Wang", "Xiaokang Chen", "Xiaokang Zhang", "Xiaotao Nie", "Xin Cheng",
            "Xin Liu", "Xin Xie", "Xingchao Liu", "Xingkai Yu", "Xingyou Li", "Xinyu Yang",
            "Xinyuan Li", "Xu Chen", "Xuecheng Su", "Xuehai Pan", "Xuheng Lin", "Xuwei Fu",
            "Y.Q. Wang", "Yang Zhang", "Yanhong Xu", "Yanru Ma", "Yao Li", "Yao Zhao",
            "Yaofeng Sun", "Yaohui Wang", "Yi Qian", "Yi Yu", "Yichao Zhang",
            "Yifan Ding", "Yifan Shi", "Yiliang Xiong", "Ying He", "Ying Zhou",
            "Yinmin Zhong", "Yishi Piao", "Yisong Wang", "Yixiao Chen", "Yixuan Tan",
            "Yixuan Wei", "Yiyang Ma", "Yiyuan Liu", "Yonglun Yang", "Yongqiang Guo",
            "Yongtong Wu", "Yu Wu", "Yuan Cheng", "Yuan Ou", "Yuanfan Xu", "Yuduan Wang",
            "Yue Gong", "Yuhan Wu", "Yuheng Zou", "Yukun Li", "Yunfan Xiong", "Yuxiang Luo",
            "Yuxiang You", "Yuxuan Liu", "Yuyang Zhou", "Z.F. Wu", "Z.Z. Ren", "Zehua Zhao",
            "Zehui Ren", "Zhangli Sha", "Zhe Fu", "Zhean Xu", "Zhenda Xie", "Zhengyan Zhang",
            "Zhewen Hao", "Zhibin Gou", "Zhicheng Ma", "Zhigang Yan", "Zhihong Shao",
            "Zhixian Huang", "Zhiyu Wu", "Zhuoshu Li", "Zhuping Zhang", "Zian Xu",
            "Zihao Wang", "Zihui Gu", "Zijia Zhu", "Zilin Li", "Zipeng Zhang", "Ziwei Xie",
            "Ziyi Gao", "Zizheng Pan", "Zongqing Yao",
            "Bei Feng", "Hui Li", "J.L. Cai", "Jiaqi Ni", "Lei Xu", "Meng Li", "Ning Tian",
            "R.J. Chen", "R.L. Jin", "S.S. Li", "Shuang Zhou", "Tianyu Sun", "X.Q. Li",
            "Xiangyue Jin", "Xiaojin Shen", "Xiaosha Chen", "Xinnan Song", "Xinyi Zhou",
            "Y.X. Zhu", "Yanping Huang", "Yaohui Li", "Yi Zheng", "Yuchen Zhu", "Yunxian Ma",
            "Zhen Huang", "Zhipeng Xu", "Zhongyu Zhang",
            "Dongjie Ji", "Jian Liang", "Jianzhong Guo", "Jin Chen", "Leyi Xia", "Miaojun Wang",
            "Mingming Li", "Peng Zhang", "Ruyi Chen", "Shangmian Sun", "Shaoqing Wu",
            "Shengfeng Ye", "T.Wang", "W.L. Xiao", "Wei An", "Xianzu Wang", "Xiaowen Sun",
            "Xiaoxiang Wang", "Ying Tang", "Yukun Zha", "Zekai Zhang", "Zhe Ju", "Zhen Zhang",
            "Zihua Qu"
        ],
        published_date="2025-12-02",
        content_type="paper"
    ),
    Document(
        url="https://arxiv.org/abs/2509.22186",
        title="MinerU2.5: A Decoupled Vision-Language Model for Efficient High-Resolution Document Parsing",
        summary="We introduce MinerU2.5, a 1.2B-parameter document parsing vision-language model that achieves state-of-the-art recognition accuracy while maintaining exceptional computational efficiency. Our approach employs a coarse-to-fine, two-stage parsing strategy that decouples global layout analysis from local content recognition. In the first stage, the model performs efficient layout analysis on downsampled images to identify structural elements, circumventing the computational overhead of processing high-resolution inputs. In the second stage, guided by the global layout, it performs targeted content recognition on native-resolution crops extracted from the original image, preserving fine-grained details in dense text, complex formulas, and tables. To support this strategy, we developed a comprehensive data engine that generates diverse, large-scale training corpora for both pretraining and fine-tuning. Ultimately, MinerU2.5 demonstrates strong document parsing ability, achieving state-of-the-art performance on multiple benchmarks, surpassing both general-purpose and domain-specific models across various recognition tasks, while maintaining significantly lower computational overhead.",
        source="arXiv",
        authors=["Junbo Niu", "Zheng Liu", "Zhuangcheng Gu", "Bin Wang", "Linke Ouyang", "Zhiyuan Zhao", "Tao Chu", "Tianyao He", "Fan Wu", "Qintong Zhang", "Zhenjiang Jin", "Guang Liang", "Rui Zhang", "Wenzheng Zhang", "Yuan Qu", "Zhifei Ren", "Yuefeng Sun", "Yuanhong Zheng", "Dongsheng Ma", "Zirui Tang", "Boyu Niu", "Ziyang Miao", "Hejun Dong", "Siyi Qian", "Junyuan Zhang", "Jingzhou Chen", "Fangdong Wang", "Xiaomeng Zhao", "Liqun Wei", "Wei Li", "Shasha Wang", "Ruiliang Xu", "Yuanyuan Cao", "Lu Chen", "Qianqian Wu", "Huaiyu Gu", "Lindong Lu", "Keming Wang", "Dechen Lin", "Guanlin Shen", "Xuanhe Zhou", "Linfeng Zhang", "Yuhang Zang", "Xiaoyi Dong", "Jiaqi Wang", "Bo Zhang", "Lei Bai", "Pei Chu", "Weijia Li", "Jiang Wu", "Lijun Wu", "Zhenxiang Li", "Guangyu Wang", "Zhongying Tu", "Chao Xu", "Kai Chen", "Yu Qiao", "Bowen Zhou", "Dahua Lin", "Wentao Zhang", "Conghui He"],
        published_date="2025-09-26",
        content_type="paper"
    ),
    Document(
        url="https://arxiv.org/abs/2512.17052v1",
        title="Dynamic Tool Dependency Retrieval for Efficient Function Calling",
        summary="Function calling agents powered by Large Language Models (LLMs) select external tools to automate complex tasks. On-device agents typically use a retrieval module to select relevant tools, improving performance and reducing context length. However, existing retrieval methods rely on static and limited inputs, failing to capture multi-step tool dependencies and evolving task context. This limitation often introduces irrelevant tools that mislead the agent, degrading efficiency and accuracy. We propose Dynamic Tool Dependency Retrieval (DTDR), a lightweight retrieval method that conditions on both the initial query and the evolving execution context. DTDR models tool dependencies from function calling demonstrations, enabling adaptive retrieval as plans unfold. We benchmark DTDR against state-of-the-art retrieval methods across multiple datasets and LLM backbones, evaluating retrieval precision, downstream task accuracy, and computational efficiency. Additionally, we explore strategies to integrate retrieved tools into prompts. Our results show that dynamic tool retrieval improves function calling success rates between  and  compared to state-of-the-art static retrievers.",
        source="arXiv",
        authors=["Bhrij Patel", "Davide Belli", "Amir Jalalirad", "Maximilian Arnold", "Aleksandr Ermovol", "Bence Major"],
        published_date="2025-12-18",
        content_type="paper"
    )
]

RELEVANT_DOCS_SECURITY = [
    Document(
        url="https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents",
        title="PromptPwnd: Prompt Injection Vulnerabilities in GitHub Actions Using AI Agents",
        summary="PromptPwnd is a new vulnerability class that affects GitHub Actions and GitLab CI/CD pipelines that use AI agents like Gemini CLI, Claude Code, and OpenAI Codex. In this vulnerability, untrusted user input from issues, pull requests, or commit messages is injected into prompts, leading to the execution of privileged tools. The attack allows secret exfiltration by tricking AI agents into leaking GITHUB_TOKEN or cloud credentials through shell commands such as gh issue edit. Google's Gemini CLI repository was confirmed vulnerable before the patch. To mitigate this, organizations should restrict AI toolsets, avoid injecting untrusted input into prompts, treat AI output as untrusted code, and limit GitHub token permissions by IP.",
        source="Aikido",
        authors=["AikRein Daelman"],
        published_date="2025-12-04",
        content_type="article"
    ),
    Document(
        url="https://chasersystems.com/blog/what-data-do-coding-agents-send-and-where-to/",
        title="What Data Do Coding Agents Send, and Where To?",
        summary="As AI coding agents become more common, security teams should understand what data these tools collect and where it goes. Chaser Systems created a test environment with seven coding agents, testing actions such as starting the agent, tab autocomplete, creating new features, committing and pushing to a git repository, running tests, and uploading data to 0x0.st. They also checked access to AWS credentials and files outside the project directory. The article describes the domains contacted, sample requests, and data transfer volumes during tests conducted with telemetry both disabled and enabled, including scenarios where telemetry is enabled, but FQDNs are blocked.",
        source="Chaser Systems",
        authors=[],
        published_date="2025-11-04",
        content_type="article"
    )
]

RELEVANT_DOCS_DATA = [
    Document(
        url="https://www.montecarlodata.com/blog-alert-fatigue-monitoring-strategy",
        title="Alert Fatigue Is Killing Your Data Quality Strategy. Here’s How to Fix It.",
        summary="Alert fatigue in data observability occurs when teams are overwhelmed by excessive, often false-positive alerts from overly rigid or unprioritized monitoring, leading to ignored notifications and stalled data quality improvements. To combat this, adopt strategies like machine learning-based monitors that learn normal data patterns to reduce noise, focus monitoring on critical tables and data products, align alert ownership with domain teams, and implement intelligent prioritization and routing based on alert type, location, and downstream impact.",
        source="Monte Carlo",
        authors=["Shohei Narron", "Ethan Post"],
        published_date="2025-12-18",
        content_type="article"
    ),
    Document(
        url="https://medium.com/@richardglew/data-testing-like-its-not-1997-part-1-c5e5b49a3a97",
        title="Data Testing Like It’s Not 1997",
        summary="Treat data quality like software quality: define what “good” means, design layered tests, and automate them across the pipeline. This cuts rework and incidents by shifting quality left while using production observability for what can't be caught earlier. Durable data quality comes from disciplined processes and ownership, not a single tool.",
        source="Medium",
        authors=["Richard Glew"],
        published_date="2025-12-8",
        content_type="article"
    ),
    Document(
        url="https://thenewstack.io/ai-agents-create-a-new-dimension-for-database-scalability/",
        title="AI Agents Create a New Dimension for Database Scalability",
        summary="The rise of AI agentic systems introduces a new scalability axis for databases: the ability to spawn and manage trillions of isolated, ephemeral database instances with microsecond provisioning and strict data isolation. Traditional multitenancy is giving way to hyper-tenancy, demanding in-process databases like SQLite, Turso, and DuckDB that offer instant instantiation, encryption, and vector-native operations. This architecture shift enables agents to fulfill dynamic, privacy-preserving data needs at hyperscale, transforming database design and operational paradigms for data-intensive organizations.",
        source="The New Stack",
        authors=["Glauber Costa"],
        published_date="2025-12-11",
        content_type="article"
    ),
    Document(
        url="https://hudi.apache.org/blog/2025/12/16/maximizing-throughput-nbcc/",
        title="Maximizing Throughput with Apache Hudi NBCC: Stop Retrying, Start Scaling",
        summary="Apache Hudi's traditional Optimistic Concurrency Control (OCC) struggles with high-concurrency writes on Merge-on-Read tables. Overlapping writes cause frequent conflicts, leading to retries, aborted work, and reduced throughput when mixing streaming and batch jobs. Non-Blocking Concurrency Control, introduced in Hudi 1.0, solves this by eliminating conflicts, allowing concurrent writers to append to separate log files, ordering commits by completion time with a TrueTime-like mechanism, and ensuring every write succeeds without retries.",
        source="Apache Hudi Blog",
        authors=[],
        published_date="2025-12-16",
        content_type="article"
    )
]

RELEVANT_DOCS_AI_ETHICS = [
    Document(
        url="https://www.ardoq.com/knowledge-hub/eu-ai-act",
        title="EU AI Act: A Complete Guide for Enterprise Architects",
        summary="The impact of Artificial Intelligence (AI) on fundamental rights and freedoms is the subject of much discussion and concern. Certainly, AI bears a lot of promise when it comes to supporting better business decisions, aiding strategic planning, and enhancing digital transformation. In response to this, the European Union (EU) has taken a step in shaping the future of AI with the recent introduction of the EU Artificial Intelligence Act. This pioneering legislation aims to establish a comprehensive legal framework for the development, deployment, and use of AI systems within the EU.",
        source="Ardoq",
        authors=["Michael Frearson"],
        published_date="2024-08-12",
        content_type="article"
    ),
    Document(
        url="https://www.techtarget.com/searchenterpriseai/tip/How-to-audit-AI-systems-for-transparency-and-compliance",
        title="How to audit AI systems for transparency and compliance",
        summary="AI audits help businesses ensure functionality, transparency and compliance when deploying AI systems. Learn how to conduct audits to build trust and meet regulatory requirements.",
        source="TechTarget",
        authors=["Kashyap Kompella"],
        published_date="2025-04-10",
        content_type="article"
    )
]

