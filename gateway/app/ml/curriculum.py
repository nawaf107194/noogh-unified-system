import logging
from typing import Any, Dict, List

logger = logging.getLogger("ml.curriculum")

CURRICULUM = {
    "computer_science": {
        "priority": "high",
        "target_examples": 1000,
        "subtopics": [
            "الخوارزميات والبنى المعطيات",
            "أنظمة التشغيل وهندسة الكمبيوتر",
            "الشبكات الحاسوبية والأمن السيبراني",
            "قواعد البيانات وأنظمة إدارة المعلومات",
            "البرمجة المتوازية والحوسبة الموزعة",
        ],
        "expert_topics": ["نظرية الحوسبة", "تعقيد الحساب", "بناء المترجمات"],
        "hub_queries": ["DsS-99/wikitext-parquet", "math_dataset", "code_search_net"],
    },
    "artificial_intelligence": {
        "priority": "high",
        "target_examples": 1200,
        "subtopics": [
            "التعلم العميق والشبكات العصبية",
            "معالجة اللغة الطبيعية (NLP)",
            "الرؤية الحاسوبية والتعرف على الصور",
            "التعلم المعزز واتخاذ القرارات",
            "الذكاء الاصطناعي التوليدي والنماذج اللغوية الكبيرة",
        ],
        "expert_topics": ["Multi-Agent RL", "Few-shot Learning", "Multimodal Architectures"],
        "hub_queries": ["wikitext", "ag_news", "scientific_papers"],
    },
    "programming": {
        "priority": "high",
        "target_examples": 800,
        "subtopics": [
            "لغات البرمجة الحديثة (Python, Rust, Go)",
            "تطوير البرمجيات وهندسة الأنظمة",
            "اختبار البرمجيات وضمان الجودة",
            "التصميم المعماري للأنظمة الكبيرة",
            "البرمجة الوظيفية والكائنية",
        ],
        "expert_topics": ["Metaprogramming", "Memory Safety in Rust", "Distributed System Design"],
        "hub_queries": ["m-a-p/CodeFeedback-Filter-v2", "codeparrot/github-code", "m-a-p/Code-Feedback"],
    },
    "mathematics": {
        "priority": "medium",
        "target_examples": 600,
        "subtopics": [
            "الجبر الخطي والحساب العددي",
            "الاحتمالات والإحصاء",
            "التفاضل والتكامل المتقدم",
            "الرياضيات المتقطعة والمنطق",
            "الرياضيات الحسابية والتحسين",
        ],
        "expert_topics": ["Optimization for ML", "Bayesian Inference", "Graph Theory"],
        "hub_queries": ["math_dataset", "gsm8k", "OFA-Sys/SocraticMath"],
    },
}

CROSS_DOMAIN_MAP = [
    {"from": "mathematics", "to": "artificial_intelligence", "theme": "Computational Math for AI"},
    {"from": "computer_science", "to": "programming", "theme": "Algorithmic Efficiency in Code"},
    {"from": "artificial_intelligence", "to": "programming", "theme": "AI-Driven Code Generation"},
    {"from": "mathematics", "to": "computer_science", "theme": "Formal Logic and Proofs"},
]


def get_curriculum(domain: str) -> Dict[str, Any]:
    """Retrieve curriculum for a specific domain."""
    return CURRICULUM.get(domain, {})


def get_all_domains() -> List[str]:
    """List all available specialization domains."""
    return list(CURRICULUM.keys())


def get_intersections() -> List[Dict]:
    """Retrieve cross-domain knowledge bridges."""
    return CROSS_DOMAIN_MAP
