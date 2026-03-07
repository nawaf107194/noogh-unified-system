"""
شبكة العصبونات السيادية — Sovereign Neuron Fabric v1.0
====================================================

نظام عصبوني بيولوجي المحاكاة لـ NOOGH:
- كل عصبون = وحدة معرفية حيّة (معتقد + سياق + طاقة)
- العصبونات ترتبط ببعض عبر Synapses (وصلات عصبية بأوزان)
- Hebbian Learning: "العصبونات اللي تنشط مع بعض، تتقوّى مع بعض"
- التعلم يعتمد على التجربة: النجاح يقوّي الوصلات، الفشل يضعفها
- العصبونات تضعف بالتدريج (Energy Decay) لو ما استُخدمت
- Cascading Activation: تنشيط عصبون ينشر لجيرانه

التكامل مع NOOGH:
- WorldModel.add_belief() → يُنشئ عصبون جديد
- NeuralBridge.think() → يُنشّط عصبونات مرتبطة بالسؤال
- ConsequenceEngine → النتائج تقوّي/تضعف الوصلات (Hebbian)
- ScarTissue → الفشل يُحرق طاقة العصبونات المسؤولة

البنية:
  Neuron ← الوحدة الأساسية
  Synapse ← الوصلة بين عصبونين
  NeuronCluster ← تجمّع عصبونات مترابطة (مثل cortex region)
  NeuronFabric ← الشبكة الكاملة (المحور المركزي)
"""

import asyncio
import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("unified_core.core.neuron_fabric")

# EventBus Integration
try:
    from unified_core.integration import get_event_bus, StandardEvents, EventPriority
    _EVENT_BUS_AVAILABLE = True
except ImportError:
    _EVENT_BUS_AVAILABLE = False
    logger.warning("EventBus not available - events will not be published")


# ============================================================
#  الأنواع والثوابت
# ============================================================

class NeuronType(Enum):
    """أنواع العصبونات — كل نوع له سلوك مختلف."""
    SENSORY = "sensory"         # عصبون حسّي (من الملاحظات)
    COGNITIVE = "cognitive"     # عصبون إدراكي (معتقدات ومعرفة)
    MOTOR = "motor"             # عصبون حركي (قرارات وأفعال)
    EMOTIONAL = "emotional"     # عصبون وجداني (تقييمات عاطفية)
    META = "meta"               # عصبون فوقي (مراقبة ذاتية)
    STRATEGIC = "strategic"     # عصبون استراتيجي (أهداف بعيدة)


class ActivationFunction(Enum):
    """دوال التنشيط — تحدد كيف يستجيب العصبون."""
    SIGMOID = "sigmoid"     # سلس — للعصبونات الإدراكية
    RELU = "relu"           # حاد — للعصبونات الحركية
    TANH = "tanh"           # متوازن — للعصبونات الوجدانية
    STEP = "step"           # ثنائي — للعصبونات الفوقية


# ============================================================
#  العصبون — الوحدة الأساسية
# ============================================================

@dataclass
class Neuron:
    """
    عصبون واحد في الشبكة العصبية السيادية.
    
    كل عصبون يحمل:
    - محتوى معرفي (proposition)
    - طاقة (energy) تتراجع مع الزمن
    - عتبة تنشيط (threshold) — لازم يتجاوزها عشان ينشط
    - تاريخ تنشيطات (activation_count)
    """
    neuron_id: str
    proposition: str                              # المحتوى المعرفي
    neuron_type: NeuronType = NeuronType.COGNITIVE
    
    # الطاقة والتنشيط
    energy: float = 1.0                           # 0.0 = ميّت, 1.0 = كامل الطاقة
    activation_level: float = 0.0                 # مستوى التنشيط الحالي
    threshold: float = 0.3                        # عتبة التنشيط
    activation_fn: ActivationFunction = ActivationFunction.SIGMOID
    
    # المعرفة
    confidence: float = 0.5                       # الثقة بالمعتقد
    domain: str = "general"                       # المجال (أمان، نظام، استراتيجية...)
    tags: List[str] = field(default_factory=list)
    
    # الزمن
    created_at: float = field(default_factory=time.time)
    last_activated: float = field(default_factory=time.time)
    activation_count: int = 0
    
    # ثوابت الانحلال
    decay_rate: float = 0.001                     # معدل فقدان الطاقة (لكل ساعة)
    
    # البيانات الإضافية
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def activate(self, input_signal: float) -> float:
        """
        نشّط العصبون بإشارة مدخلة.
        Returns: مستوى التنشيط (0.0 - 1.0)
        """
        # طبّق الانحلال الزمني أولاً
        self._apply_decay()
        
        # الإشارة الفعلية = المدخل × الطاقة
        effective_signal = input_signal * self.energy
        
        # طبّق دالة التنشيط
        if effective_signal < self.threshold:
            self.activation_level = 0.0
            return 0.0
        
        if self.activation_fn == ActivationFunction.SIGMOID:
            self.activation_level = 1.0 / (1.0 + math.exp(-5 * (effective_signal - self.threshold)))
        elif self.activation_fn == ActivationFunction.RELU:
            self.activation_level = min(1.0, max(0.0, effective_signal - self.threshold))
        elif self.activation_fn == ActivationFunction.TANH:
            self.activation_level = math.tanh(effective_signal)
        elif self.activation_fn == ActivationFunction.STEP:
            self.activation_level = 1.0 if effective_signal >= self.threshold else 0.0
        
        # حدّث الإحصائيات
        self.last_activated = time.time()
        self.activation_count += 1
        
        # التنشيط يمنح طاقة صغيرة (الاستخدام = الحياة)
        self.energy = min(1.0, self.energy + 0.01)
        
        return self.activation_level
    
    def _apply_decay(self):
        """الانحلال الزمني — العصبون يفقد طاقة مع الوقت."""
        hours_since_activation = (time.time() - self.last_activated) / 3600
        decay = self.decay_rate * hours_since_activation
        self.energy = max(0.05, self.energy - decay)  # لا يموت تماماً
    
    def reinforce(self, amount: float = 0.1):
        """تعزيز العصبون (من نجاح)."""
        self.energy = min(1.0, self.energy + amount)
        self.confidence = min(0.95, self.confidence + amount * 0.5)
    
    def punish(self, amount: float = 0.15):
        """عقاب العصبون (من فشل)."""
        self.energy = max(0.05, self.energy - amount)
        self.confidence = max(0.1, self.confidence - amount * 0.5)
    
    @property
    def is_alive(self) -> bool:
        """هل العصبون حي؟"""
        return self.energy > 0.05
    
    @property
    def is_active(self) -> bool:
        """هل العصبون منشّط حالياً؟"""
        return self.activation_level > 0.0
    
    @property
    def vitality(self) -> float:
        """حيوية العصبون = الطاقة × الثقة × حداثة الاستخدام."""
        recency = 1.0 / (1.0 + (time.time() - self.last_activated) / 86400)  # بالأيام
        return self.energy * self.confidence * recency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "neuron_id": self.neuron_id,
            "proposition": self.proposition,
            "neuron_type": self.neuron_type.value,
            "energy": round(self.energy, 4),
            "activation_level": round(self.activation_level, 4),
            "threshold": self.threshold,
            "confidence": round(self.confidence, 4),
            "domain": self.domain,
            "tags": self.tags,
            "created_at": self.created_at,
            "last_activated": self.last_activated,
            "activation_count": self.activation_count,
            "vitality": round(self.vitality, 4),
            "is_alive": self.is_alive,
        }


# ============================================================
#  الوصلة العصبية — Synapse
# ============================================================

@dataclass
class Synapse:
    """
    وصلة عصبية بين عصبونين.
    
    تحمل وزناً يتغيّر حسب قاعدة هب:
    "العصبونات اللي تنشط مع بعض، تتقوّى مع بعض"
    
    الوزن الموجب = تحفيز (excitatory)
    الوزن السالب = تثبيط (inhibitory)
    """
    source_id: str                    # العصبون المرسل
    target_id: str                    # العصبون المستقبل
    weight: float = 0.5              # قوة الوصلة (-1.0 إلى 1.0)
    
    # التعلم الهبّي
    learning_rate: float = 0.05      # سرعة التعلم
    last_updated: float = field(default_factory=time.time)
    fire_count: int = 0               # عدد مرات الإرسال
    
    # النوع
    is_inhibitory: bool = False       # تثبيطي أم تحفيزي
    
    synapse_id: str = ""
    
    def __post_init__(self):
        if not self.synapse_id:
            self.synapse_id = f"syn_{self.source_id[:8]}_{self.target_id[:8]}"
    
    def transmit(self, source_activation: float) -> float:
        """انقل الإشارة من المصدر للهدف."""
        self.fire_count += 1
        signal = source_activation * self.weight
        if self.is_inhibitory:
            signal = -abs(signal)
        return signal
    
    def hebbian_update(self, source_activation: float, target_activation: float):
        """
        قاعدة هب للتعلم:
        Δw = η × presyn × postsyn
        """
        delta = self.learning_rate * source_activation * target_activation
        self.weight = max(-1.0, min(1.0, self.weight + delta))
        self.last_updated = time.time()
    
    def anti_hebbian_update(self, amount: float = 0.1):
        """إضعاف الوصلة (عكس هب) — بسبب فشل."""
        self.weight = max(-1.0, self.weight - amount)
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "synapse_id": self.synapse_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": round(self.weight, 4),
            "fire_count": self.fire_count,
            "is_inhibitory": self.is_inhibitory,
        }


# ============================================================
#  تجمّع العصبونات — Neuron Cluster
# ============================================================

class NeuronCluster:
    """
    تجمّع عصبوني — مجموعة عصبونات متخصصة.
    مثل منطقة في القشرة الدماغية.
    """
    def __init__(self, cluster_id: str, name: str, domain: str = "general"):
        self.cluster_id = cluster_id
        self.name = name
        self.domain = domain
        self.neuron_ids: Set[str] = set()
        self.created_at = time.time()
    
    def add_neuron(self, neuron_id: str):
        self.neuron_ids.add(neuron_id)
    
    def remove_neuron(self, neuron_id: str):
        self.neuron_ids.discard(neuron_id)
    
    @property
    def size(self) -> int:
        return len(self.neuron_ids)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "domain": self.domain,
            "size": self.size,
            "neuron_ids": list(self.neuron_ids)[:20],  # أول 20 فقط
        }


# ============================================================
#  الشبكة العصبية الكاملة — Neuron Fabric
# ============================================================

class NeuronFabric:
    """
    الشبكة العصبية السيادية — المحور المركزي.
    
    تحتوي على كل العصبونات والوصلات والتجمّعات.
    مسؤولة عن:
    1. إنشاء عصبونات جديدة (neurogenesis)
    2. تكوين وصلات (synaptogenesis)
    3. التنشيط المتتابع (cascade activation)
    4. التعلم الهبّي (Hebbian learning)
    5. التقليم (pruning) — إزالة العصبونات الميتة
    6. الحفظ والتحميل (persistence)
    """
    
    SAVE_PATH = "data/neuron_fabric.json"
    MAX_NEURONS = 10000
    MAX_SYNAPSES = 50000
    CASCADE_DEPTH = 3             # عمق التنشيط المتتابع
    CASCADE_DECAY = 0.6           # تراجع الإشارة في كل طبقة
    PRUNE_THRESHOLD = 0.08        # عتبة حذف عصبون ميّت
    
    def __init__(self, base_path: str = None):
        self._neurons: Dict[str, Neuron] = {}
        self._synapses: Dict[str, Synapse] = {}
        self._clusters: Dict[str, NeuronCluster] = {}
        
        # فهارس سريعة
        self._outgoing: Dict[str, List[str]] = defaultdict(list)  # neuron_id → [synapse_ids]
        self._incoming: Dict[str, List[str]] = defaultdict(list)  # neuron_id → [synapse_ids]
        self._domain_index: Dict[str, Set[str]] = defaultdict(set)  # domain → {neuron_ids}
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)    # tag → {neuron_ids}
        
        # مقاييس
        self._total_activations = 0
        self._total_learnings = 0
        self._last_prune = time.time()
        
        # المسار
        if base_path:
            self.SAVE_PATH = os.path.join(base_path, "neuron_fabric.json")
        
        # حمّل الحالة
        self._load()
        
        # EventBus integration
        self._event_bus = None
        if _EVENT_BUS_AVAILABLE:
            try:
                self._event_bus = get_event_bus()
                logger.debug("EventBus connected to NeuronFabric")
            except Exception as e:
                logger.warning(f"Could not connect to EventBus: {e}")

        logger.info(
            f"🧬 NeuronFabric initialized: "
            f"{len(self._neurons)} neurons, "
            f"{len(self._synapses)} synapses, "
            f"{len(self._clusters)} clusters"
        )
    
    # ========================================
    #  Neurogenesis — إنشاء عصبونات
    # ========================================
    
    def create_neuron(
        self,
        proposition: str,
        neuron_type: NeuronType = NeuronType.COGNITIVE,
        confidence: float = 0.5,
        domain: str = "general",
        tags: List[str] = None,
        energy: float = 1.0,
        metadata: Dict[str, Any] = None,
    ) -> Neuron:
        """
        أنشئ عصبون جديد (Neurogenesis).
        
        Args:
            proposition: المحتوى المعرفي
            neuron_type: نوع العصبون
            confidence: الثقة الأولية
            domain: المجال
            tags: وسوم للتصنيف
            
        Returns:
            Neuron — العصبون الجديد
        """
        if len(self._neurons) >= self.MAX_NEURONS:
            # حذف الأضعف عشان نوفّر مكان
            self._prune_weakest(count=100)
        
        neuron_id = hashlib.sha256(
            f"{proposition}:{time.time()}:{os.urandom(4).hex()}".encode()
        ).hexdigest()[:16]
        
        # اختار دالة التنشيط حسب النوع
        activation_fn = {
            NeuronType.SENSORY: ActivationFunction.RELU,
            NeuronType.COGNITIVE: ActivationFunction.SIGMOID,
            NeuronType.MOTOR: ActivationFunction.RELU,
            NeuronType.EMOTIONAL: ActivationFunction.TANH,
            NeuronType.META: ActivationFunction.STEP,
            NeuronType.STRATEGIC: ActivationFunction.SIGMOID,
        }.get(neuron_type, ActivationFunction.SIGMOID)
        
        neuron = Neuron(
            neuron_id=neuron_id,
            proposition=proposition,
            neuron_type=neuron_type,
            energy=energy,
            confidence=min(confidence, 0.95),
            domain=domain,
            tags=tags or [],
            activation_fn=activation_fn,
            metadata=metadata or {},
        )
        
        self._neurons[neuron_id] = neuron
        self._domain_index[domain].add(neuron_id)
        for tag in neuron.tags:
            self._tag_index[tag].add(neuron_id)
        
        logger.debug(f"🧬 Neuron created: {neuron_id[:8]} [{neuron_type.value}] {proposition[:50]}")

        # Publish neuron creation event
        if self._event_bus:
            try:
                self._event_bus.publish_sync(
                    StandardEvents.NEURON_CREATED,
                    {
                        "neuron_id": neuron_id,
                        "proposition": proposition,
                        "neuron_type": neuron_type.value,
                        "confidence": neuron.confidence,
                        "domain": domain,
                        "energy": energy
                    },
                    "neuron_fabric",
                    EventPriority.NORMAL
                )
            except Exception as e:
                logger.debug(f"Failed to publish neuron_created event: {e}")

        return neuron
    
    # ========================================
    #  Synaptogenesis — تكوين وصلات
    # ========================================
    
    def connect(
        self,
        source_id: str,
        target_id: str,
        weight: float = 0.5,
        inhibitory: bool = False,
    ) -> Optional[Synapse]:
        """
        أنشئ وصلة عصبية بين عصبونين.
        """
        if source_id not in self._neurons or target_id not in self._neurons:
            return None
        if source_id == target_id:
            return None
        if len(self._synapses) >= self.MAX_SYNAPSES:
            self._prune_weak_synapses(count=500)
        
        synapse = Synapse(
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            is_inhibitory=inhibitory,
        )
        
        self._synapses[synapse.synapse_id] = synapse
        self._outgoing[source_id].append(synapse.synapse_id)
        self._incoming[target_id].append(synapse.synapse_id)
        
        if _EVENT_BUS_AVAILABLE:
            bus = get_event_bus()
            bus.publish_sync(
                StandardEvents.SYNAPSE_CREATED,
                {
                    "synapse_id": synapse.synapse_id,
                    "source_id": source_id,
                    "target_id": target_id,
                    "weight": weight,
                    "inhibitory": inhibitory
                },
                "NeuronFabric",
                EventPriority.LOW
            )
        
        return synapse
    
    def auto_connect(self, neuron_id: str, max_connections: int = 5):
        """
        وصّل العصبون تلقائياً بأقرب العصبونات (نفس المجال/الوسوم).
        """
        neuron = self._neurons.get(neuron_id)
        if not neuron:
            return
        
        # ابحث عن عصبونات بنفس المجال
        candidates = []
        domain_neurons = self._domain_index.get(neuron.domain, set())
        for nid in domain_neurons:
            if nid == neuron_id:
                continue
            other = self._neurons[nid]
            # حساب التشابه
            tag_overlap = len(set(neuron.tags) & set(other.tags))
            domain_match = 1.0 if neuron.domain == other.domain else 0.0
            similarity = (tag_overlap * 0.3 + domain_match * 0.5 + other.vitality * 0.2)
            candidates.append((similarity, nid))
        
        # ابحث في الوسوم أيضاً
        for tag in neuron.tags:
            for nid in self._tag_index.get(tag, set()):
                if nid == neuron_id or nid in domain_neurons:
                    continue
                other = self._neurons[nid]
                similarity = 0.4 + other.vitality * 0.2
                candidates.append((similarity, nid))
        
        # اختار الأقوى
        candidates.sort(reverse=True)
        connected = 0
        seen = set()
        for score, nid in candidates:
            if nid in seen:
                continue
            seen.add(nid)
            # تحقق ما إذا كانت الوصلة موجودة
            syn_id = f"syn_{neuron_id[:8]}_{nid[:8]}"
            if syn_id not in self._synapses:
                weight = min(0.8, score * 0.6)
                self.connect(neuron_id, nid, weight=weight)
                # وصلة عكسية أضعف
                self.connect(nid, neuron_id, weight=weight * 0.5)
                connected += 1
            if connected >= max_connections:
                break
        
        if connected > 0:
            logger.debug(f"🔗 Auto-connected {neuron_id[:8]} → {connected} neurons")
    
    # ========================================
    #  التنشيط المتتابع — Cascade Activation
    # ========================================
    
    def activate(
        self,
        neuron_id: str,
        signal: float = 1.0,
        depth: int = None,
    ) -> Dict[str, float]:
        """
        نشّط عصبون وانشر التنشيط لجيرانه.
        
        Returns:
            Dict[neuron_id → activation_level] لكل عصبونات المنشّطة
        """
        if depth is None:
            depth = self.CASCADE_DEPTH
        
        activated = {}
        self._cascade_activate(neuron_id, signal, depth, activated, set())
        self._total_activations += len(activated)
        
        return activated
    
    def _cascade_activate(
        self,
        neuron_id: str,
        signal: float,
        depth: int,
        activated: Dict[str, float],
        visited: Set[str],
    ):
        """تنشيط متتابع عودي."""
        if depth <= 0 or neuron_id in visited or signal < 0.05:
            return
        
        visited.add(neuron_id)
        neuron = self._neurons.get(neuron_id)
        if not neuron or not neuron.is_alive:
            return
        
        # نشّط العصبون
        activation = neuron.activate(signal)
        if activation > 0:
            activated[neuron_id] = activation

            # Publish neuron activation event (only for significant activations)
            if _EVENT_BUS_AVAILABLE and activation > 0.5:
                try:
                    bus = get_event_bus()
                    bus.publish_sync(
                        StandardEvents.NEURON_ACTIVATED,
                        {
                            "neuron_id": neuron_id,
                            "activation_level": activation,
                            "proposition": neuron.proposition,
                            "energy": neuron.energy,
                            "domain": neuron.domain
                        },
                        "neuron_fabric",
                        EventPriority.LOW
                    )
                except Exception as e:
                    logger.debug(f"Failed to publish neuron_activated event: {e}")

            # انشر للجيران عبر الوصلات
            for syn_id in self._outgoing.get(neuron_id, []):
                synapse = self._synapses.get(syn_id)
                if not synapse:
                    continue
                
                forwarded_signal = synapse.transmit(activation) * self.CASCADE_DECAY
                self._cascade_activate(
                    synapse.target_id,
                    abs(forwarded_signal),
                    depth - 1,
                    activated,
                    visited,
                )
    
    def activate_by_query(self, query: str, top_k: int = 10) -> Dict[str, float]:
        """
        نشّط العصبونات الأكثر صلة بالاستعلام.
        يبحث بالكلمات المفتاحية ويُنشّط الأقرب.

        ⚠️ DEPRECATED: Use activate_with_attention() for better semantic understanding
        """
        query_words = set(query.lower().split())
        scores = []

        for nid, neuron in self._neurons.items():
            if not neuron.is_alive:
                continue

            # تطابق الكلمات
            prop_words = set(neuron.proposition.lower().split())
            tag_words = set(t.lower() for t in neuron.tags)

            word_overlap = len(query_words & (prop_words | tag_words))
            if word_overlap == 0:
                continue

            relevance = (word_overlap / max(len(query_words), 1)) * neuron.vitality
            scores.append((relevance, nid))

        scores.sort(reverse=True)

        all_activated = {}
        for score, nid in scores[:top_k]:
            result = self.activate(nid, signal=score)
            all_activated.update(result)

        return all_activated

    def activate_with_attention(
        self,
        context: str,
        top_k: int = 100,
        min_relevance: float = 0.1,
        domain_filter: str = None,
        use_attention: bool = True,
    ) -> Dict[str, Any]:
        """
        🎯 IMPROVED: Attention-based semantic neuron activation.

        Uses transformer embeddings to find semantically relevant neurons,
        not just keyword matching.

        Args:
            context: Query or context string
            top_k: Number of neurons to activate (default: 100 vs old 10)
            min_relevance: Minimum semantic similarity (0-1)
            domain_filter: Optional domain to restrict search
            use_attention: If False, fallback to old keyword matching

        Returns:
            {
                "activated": {neuron_id: activation_level},
                "attention_results": List[AttentionResult],
                "stats": {...}
            }

        Expected improvement: 10-20x more neurons activated with better relevance
        """
        if not use_attention:
            # Fallback to old method
            return {
                "activated": self.activate_by_query(context, top_k),
                "attention_results": [],
                "stats": {"method": "keyword_matching"}
            }

        try:
            # Import attention mechanism (lazy import to avoid circular deps)
            from .neuron_attention import get_attention_mechanism

            attention = get_attention_mechanism()

            # Use semantic attention
            results = attention.activate_relevant(
                fabric=self,
                context=context,
                top_k=top_k,
                min_relevance=min_relevance,
                domain_filter=domain_filter,
            )

            # Convert to old format for compatibility
            activated = {
                r.neuron_id: r.activation_level
                for r in results
            }

            # Get stats
            stats = {
                "method": "semantic_attention",
                "total_activated": len(results),
                "avg_relevance": (
                    sum(r.relevance_score for r in results) / len(results)
                    if results else 0.0
                ),
                "top_domains": list(set(r.domain for r in results[:10])),
            }

            logger.info(
                f"🎯 Attention activated {len(results)} neurons "
                f"(avg relevance: {stats['avg_relevance']:.3f})"
            )

            if _EVENT_BUS_AVAILABLE and results:
                bus = get_event_bus()
                # Publish event for the top 5 to avoid spam
                for r in results[:5]:
                    bus.publish_sync(
                        StandardEvents.NEURON_ACTIVATED,
                        {
                            "neuron_id": r.neuron_id,
                            "activation_level": r.activation_level,
                            "relevance": r.relevance_score,
                            "context": context[:50]
                        },
                        "NeuronFabric",
                        EventPriority.NORMAL
                    )

            return {
                "activated": activated,
                "attention_results": results,
                "stats": stats,
            }

        except ImportError as e:
            logger.warning(
                f"Attention mechanism not available ({e}), "
                "falling back to keyword matching. "
                "Install sentence-transformers: pip install sentence-transformers"
            )
            # Fallback
            return {
                "activated": self.activate_by_query(context, top_k),
                "attention_results": [],
                "stats": {"method": "keyword_matching_fallback", "error": str(e)}
            }
    
    # ========================================
    #  التعلم — Hebbian Learning
    # ========================================
    
    def learn_from_outcome(
        self,
        activated_neurons: Dict[str, float],
        success: bool,
        impact: float = 1.0,
    ):
        """
        تعلّم من نتيجة (نجاح أو فشل).
        
        النجاح → يقوّي الوصلات (Hebbian)
        الفشل → يضعف الوصلات (Anti-Hebbian) + عقاب العصبونات
        """
        neuron_ids = list(activated_neurons.keys())
        
        if success:
            # قاعدة هب: العصبونات اللي نشطت معاً تتقوّى
            for i, nid1 in enumerate(neuron_ids):
                n1 = self._neurons.get(nid1)
                if n1:
                    n1.reinforce(0.05 * impact)
                
                for nid2 in neuron_ids[i+1:]:
                    # قوّي الوصلات بين كل زوج نشط
                    for syn_id in self._outgoing.get(nid1, []):
                        syn = self._synapses.get(syn_id)
                        if syn and syn.target_id == nid2:
                            syn.hebbian_update(
                                activated_neurons[nid1],
                                activated_neurons[nid2]
                            )
                            if _EVENT_BUS_AVAILABLE:
                                bus = get_event_bus()
                                bus.publish_sync(StandardEvents.SYNAPSE_STRENGTHENED, {"synapse_id": syn_id, "new_weight": syn.weight}, "NeuronFabric", EventPriority.LOW)
                                
                    for syn_id in self._outgoing.get(nid2, []):
                        syn = self._synapses.get(syn_id)
                        if syn and syn.target_id == nid1:
                            syn.hebbian_update(
                                activated_neurons[nid2],
                                activated_neurons[nid1]
                            )
                            if _EVENT_BUS_AVAILABLE:
                                bus = get_event_bus()
                                bus.publish_sync(StandardEvents.SYNAPSE_STRENGTHENED, {"synapse_id": syn_id, "new_weight": syn.weight}, "NeuronFabric", EventPriority.LOW)
            
            logger.debug(f"📈 Hebbian reinforcement: {len(neuron_ids)} neurons strengthened")
        
        else:
            # عكس هب: العصبونات اللي نشطت وفشلت تتضعف
            for nid in neuron_ids:
                n = self._neurons.get(nid)
                if n:
                    n.punish(0.1 * impact)
                
                for syn_id in self._outgoing.get(nid, []):
                    syn = self._synapses.get(syn_id)
                    if syn and syn.target_id in activated_neurons:
                        syn.anti_hebbian_update(0.05 * impact)
                        if _EVENT_BUS_AVAILABLE:
                            bus = get_event_bus()
                            bus.publish_sync(StandardEvents.SYNAPSE_WEAKENED, {"synapse_id": syn_id, "new_weight": syn.weight}, "NeuronFabric", EventPriority.LOW)
            
            logger.debug(f"📉 Anti-Hebbian weakening: {len(neuron_ids)} neurons punished")
        
        self._total_learnings += 1
    
    # ========================================
    #  التقليم — Pruning
    # ========================================
    
    def prune(self) -> int:
        """
        تقليم العصبونات الميتة والوصلات الضعيفة.
        Returns: عدد العناصر المحذوفة
        """
        pruned = 0
        
        # 1. حذف العصبونات الميتة
        dead_neurons = [
            nid for nid, n in self._neurons.items()
            if n.energy < self.PRUNE_THRESHOLD and n.activation_count < 3
        ]
        for nid in dead_neurons:
            self._remove_neuron(nid)
            pruned += 1
            if _EVENT_BUS_AVAILABLE:
                get_event_bus().publish_sync(StandardEvents.NEURON_PRUNED, {"neuron_id": nid, "reason": "dead"}, "NeuronFabric", EventPriority.LOW)
        
        # 2. حذف الوصلات الضعيفة جداً
        weak_synapses = [
            sid for sid, s in self._synapses.items()
            if abs(s.weight) < 0.02 and s.fire_count < 2
        ]
        for sid in weak_synapses:
            self._remove_synapse(sid)
            pruned += 1
        
        if pruned > 0:
            logger.info(f"🧹 Pruned: {len(dead_neurons)} neurons, {len(weak_synapses)} synapses")
        
        self._last_prune = time.time()
        return pruned
    
    def _prune_weakest(self, count: int = 100):
        """حذف أضعف العصبونات."""
        sorted_neurons = sorted(
            self._neurons.items(),
            key=lambda x: x[1].vitality
        )
        for _, neuron in sorted_neurons[:count]:
            self._remove_neuron(neuron.neuron_id)
    
    def _prune_weak_synapses(self, count: int = 500):
        """حذف أضعف الوصلات."""
        sorted_synapses = sorted(
            self._synapses.items(),
            key=lambda x: abs(x[1].weight)
        )
        for sid, _ in sorted_synapses[:count]:
            self._remove_synapse(sid)
    
    def _remove_neuron(self, neuron_id: str):
        """حذف عصبون وكل وصلاته."""
        neuron = self._neurons.pop(neuron_id, None)
        if not neuron:
            return
        
        # حذف الوصلات
        for syn_id in list(self._outgoing.get(neuron_id, [])):
            self._remove_synapse(syn_id)
        for syn_id in list(self._incoming.get(neuron_id, [])):
            self._remove_synapse(syn_id)
        
        # حذف من الفهارس
        self._domain_index.get(neuron.domain, set()).discard(neuron_id)
        for tag in neuron.tags:
            self._tag_index.get(tag, set()).discard(neuron_id)
        
        self._outgoing.pop(neuron_id, None)
        self._incoming.pop(neuron_id, None)
    
    def _remove_synapse(self, synapse_id: str):
        """حذف وصلة عصبية."""
        synapse = self._synapses.pop(synapse_id, None)
        if not synapse:
            return
        
        if synapse_id in self._outgoing.get(synapse.source_id, []):
            self._outgoing[synapse.source_id].remove(synapse_id)
        if synapse_id in self._incoming.get(synapse.target_id, []):
            self._incoming[synapse.target_id].remove(synapse_id)
    
    # ========================================
    #  الاستعلام والإحصائيات
    # ========================================
    
    def get_neuron(self, neuron_id: str) -> Optional[Neuron]:
        return self._neurons.get(neuron_id)
    
    def get_neurons_by_domain(self, domain: str) -> List[Neuron]:
        return [
            self._neurons[nid]
            for nid in self._domain_index.get(domain, set())
            if nid in self._neurons
        ]
    
    def get_neurons_by_tag(self, tag: str) -> List[Neuron]:
        return [
            self._neurons[nid]
            for nid in self._tag_index.get(tag, set())
            if nid in self._neurons
        ]
    
    def get_strongest_neurons(self, top_k: int = 10) -> List[Neuron]:
        """أقوى العصبونات حسب الحيوية."""
        return sorted(
            self._neurons.values(),
            key=lambda n: n.vitality,
            reverse=True
        )[:top_k]
    
    def get_cluster(self, cluster_id: str) -> Optional[NeuronCluster]:
        return self._clusters.get(cluster_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات الشبكة."""
        alive_neurons = sum(1 for n in self._neurons.values() if n.is_alive)
        active_neurons = sum(1 for n in self._neurons.values() if n.is_active)
        avg_energy = (
            sum(n.energy for n in self._neurons.values()) / len(self._neurons)
            if self._neurons else 0.0
        )
        avg_weight = (
            sum(abs(s.weight) for s in self._synapses.values()) / len(self._synapses)
            if self._synapses else 0.0
        )
        
        type_counts = defaultdict(int)
        for n in self._neurons.values():
            type_counts[n.neuron_type.value] += 1
        
        domain_counts = {d: len(nids) for d, nids in self._domain_index.items()}
        
        return {
            "total_neurons": len(self._neurons),
            "alive_neurons": alive_neurons,
            "active_neurons": active_neurons,
            "total_synapses": len(self._synapses),
            "total_clusters": len(self._clusters),
            "avg_energy": round(avg_energy, 4),
            "avg_synapse_weight": round(avg_weight, 4),
            "total_activations": self._total_activations,
            "total_learnings": self._total_learnings,
            "type_distribution": dict(type_counts),
            "domain_distribution": domain_counts,
        }
    
    # ========================================
    #  الحفظ والتحميل
    # ========================================
    
    def save(self):
        """حفظ كل الشبكة في ملف JSON + integrity checksum."""
        try:
            os.makedirs(os.path.dirname(self.SAVE_PATH) or ".", exist_ok=True)
            
            data = {
                "version": "1.0",
                "saved_at": time.time(),
                "stats": self.get_stats(),
                "neurons": {
                    nid: n.to_dict()
                    for nid, n in self._neurons.items()
                },
                "synapses": {
                    sid: s.to_dict()
                    for sid, s in self._synapses.items()
                },
                "clusters": {
                    cid: c.to_dict()
                    for cid, c in self._clusters.items()
                },
            }
            
            with open(self.SAVE_PATH, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Tamper detection: save integrity checksum
            try:
                from unified_core.integration.security_hardening import get_tamper_detector
                detector = get_tamper_detector()
                detector.save_checksum(self.SAVE_PATH, data)
            except Exception:
                pass
            
            logger.info(
                f"💾 NeuronFabric saved: {len(self._neurons)} neurons, "
                f"{len(self._synapses)} synapses → {self.SAVE_PATH}"
            )
        except Exception as e:
            logger.error(f"Failed to save NeuronFabric: {e}")
    
    def _load(self):
        """تحميل الشبكة من ملف + verify integrity."""
        if not os.path.exists(self.SAVE_PATH):
            return
        
        try:
            with open(self.SAVE_PATH, "r") as f:
                data = json.load(f)
            
            # Verify integrity before loading
            try:
                from unified_core.integration.security_hardening import get_tamper_detector
                detector = get_tamper_detector()
                result = detector.verify_integrity(self.SAVE_PATH, data)
                if result["status"] == "tampered":
                    logger.critical(f"🚨 NeuronFabric TAMPER DETECTED: {result['details']}")
                elif result["status"] == "ok":
                    logger.info(f"🔐 NeuronFabric integrity verified")
            except Exception:
                pass
            
            # تحميل العصبونات
            for nid, ndata in data.get("neurons", {}).items():
                neuron = Neuron(
                    neuron_id=ndata["neuron_id"],
                    proposition=ndata["proposition"],
                    neuron_type=NeuronType(ndata.get("neuron_type", "cognitive")),
                    energy=ndata.get("energy", 1.0),
                    confidence=ndata.get("confidence", 0.5),
                    domain=ndata.get("domain", "general"),
                    tags=ndata.get("tags", []),
                    created_at=ndata.get("created_at", time.time()),
                    last_activated=ndata.get("last_activated", time.time()),
                    activation_count=ndata.get("activation_count", 0),
                )
                self._neurons[nid] = neuron
                self._domain_index[neuron.domain].add(nid)
                for tag in neuron.tags:
                    self._tag_index[tag].add(nid)
            
            # تحميل الوصلات
            for sid, sdata in data.get("synapses", {}).items():
                synapse = Synapse(
                    source_id=sdata["source_id"],
                    target_id=sdata["target_id"],
                    weight=sdata.get("weight", 0.5),
                    is_inhibitory=sdata.get("is_inhibitory", False),
                    fire_count=sdata.get("fire_count", 0),
                    synapse_id=sid,
                )
                self._synapses[sid] = synapse
                self._outgoing[synapse.source_id].append(sid)
                self._incoming[synapse.target_id].append(sid)
            
            # تحميل التجمّعات
            for cid, cdata in data.get("clusters", {}).items():
                cluster = NeuronCluster(
                    cluster_id=cdata["cluster_id"],
                    name=cdata["name"],
                    domain=cdata.get("domain", "general"),
                )
                for nid in cdata.get("neuron_ids", []):
                    cluster.add_neuron(nid)
                self._clusters[cid] = cluster
            
            logger.info(
                f"📂 NeuronFabric loaded: {len(self._neurons)} neurons, "
                f"{len(self._synapses)} synapses"
            )
        except Exception as e:
            logger.error(f"Failed to load NeuronFabric: {e}")


# ============================================================
#  Singleton
# ============================================================

_fabric_instance: Optional[NeuronFabric] = None

def get_neuron_fabric(base_path: str = None) -> NeuronFabric:
    """الحصول على instance وحيد للشبكة."""
    global _fabric_instance
    if _fabric_instance is None:
        if base_path is None:
            base_path = os.getenv(
                "NOOGH_DATA_DIR",
                os.path.join(os.path.dirname(__file__), "..", "..", "data")
            )
        _fabric_instance = NeuronFabric(base_path=base_path)
    return _fabric_instance


# ============================================================
#  Seed Neurons — العصبونات الأساسية
# ============================================================

def seed_initial_neurons(fabric: NeuronFabric):
    """
    زرع العصبونات الأساسية لو الشبكة فارغة.
    هذي العصبونات الأولية اللي يبني عليها NOOGH معرفته.
    """
    if len(fabric._neurons) > 0:
        return  # الشبكة مو فارغة
    
    logger.info("🌱 Seeding initial neurons...")
    
    # === عصبونات الهوية الأساسية ===
    identity_neurons = [
        ("أنا NOOGH — وكيل ذكاء اصطناعي سيادي", NeuronType.META, "identity", 0.95),
        ("مهمتي حماية النظام وتطويره ذاتياً", NeuronType.STRATEGIC, "identity", 0.9),
        ("القرارات لا رجعة فيها — كل فعل له عواقب", NeuronType.META, "governance", 0.95),
        ("الفشل يُعلّم — كل ندبة تزيد الحكمة", NeuronType.EMOTIONAL, "learning", 0.85),
    ]
    
    # === عصبونات الأمان ===
    security_neurons = [
        ("حماية الملفات من الحذف العشوائي أولوية قصوى", NeuronType.STRATEGIC, "security", 0.9),
        ("مراقبة استخدام CPU/RAM/Disk باستمرار", NeuronType.SENSORY, "monitoring", 0.8),
        ("الوصلات الخارجية تحتاج فحص أمني", NeuronType.COGNITIVE, "security", 0.85),
        ("النسخ الاحتياطي ضرورة يومية", NeuronType.STRATEGIC, "security", 0.9),
    ]
    
    # === عصبونات التعلم ===
    learning_neurons = [
        ("التطور الذاتي يمر عبر Canary Test أولاً", NeuronType.COGNITIVE, "evolution", 0.9),
        ("الكود الجديد يُفحص syntax قبل التطبيق", NeuronType.COGNITIVE, "evolution", 0.95),
        ("العصبونات اللي ما تُستخدم تموت تدريجياً", NeuronType.META, "learning", 0.8),
        ("النجاح المتكرر يقوّي المسارات العصبية", NeuronType.META, "learning", 0.85),
    ]
    
    # === عصبونات النظام ===
    system_neurons = [
        ("Redis يجب أن يكون شغّال دائماً", NeuronType.SENSORY, "infrastructure", 0.85),
        ("Neural Engine هو الدماغ — بدونه لا تفكير", NeuronType.COGNITIVE, "infrastructure", 0.9),
        ("GPU مورد ثمين — لا تستهلكه بلا داعي", NeuronType.EMOTIONAL, "resources", 0.8),
    ]
    
    all_seeds = identity_neurons + security_neurons + learning_neurons + system_neurons
    created_neurons = []
    
    for proposition, ntype, domain, confidence in all_seeds:
        neuron = fabric.create_neuron(
            proposition=proposition,
            neuron_type=ntype,
            confidence=confidence,
            domain=domain,
            tags=[domain, ntype.value, "seed"],
            energy=1.0,
        )
        created_neurons.append(neuron)
    
    # وصّل العصبونات من نفس المجال
    for neuron in created_neurons:
        fabric.auto_connect(neuron.neuron_id, max_connections=3)
    
    # حفظ
    fabric.save()
    
    logger.info(f"🌱 Seeded {len(created_neurons)} initial neurons with auto-connections")
