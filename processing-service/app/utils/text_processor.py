import re
import logging
from typing import Dict, Any, List, Optional, Set
import jieba
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy

logger = logging.getLogger(__name__)

# 加载模型
try:
    nlp_zh = spacy.load("zh_core_web_sm")
    nlp_en = spacy.load("en_core_web_sm")
    logger.info("SpaCy模型加载成功")
except Exception as e:
    logger.warning(f"SpaCy模型加载失败: {e}")
    nlp_zh = None
    nlp_en = None

# 停用词
try:
    stop_words_en = set(stopwords.words('english'))
    logger.info("英文停用词加载成功")
except Exception as e:
    logger.warning(f"英文停用词加载失败: {e}")
    stop_words_en = set()

# 中文停用词（简单示例，实际应用中可能需要更完整的停用词表）
stop_words_zh = {
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "着",
    "或", "一个", "没有", "我们", "你们", "他们", "它们", "这个",
    "那个", "这些", "那些", "这样", "那样", "之", "的话", "什么",
    "如何", "怎么", "为什么", "因为", "所以", "但是", "可是", "然而"
}

class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    def clean_text(text: str, language: str = "zh") -> str:
        """
        基本文本清洗
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 移除多余空格
        text = " ".join(text.split())
        
        # 移除URL
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 移除HTML标签
        text = re.sub(r'<.*?>', '', text)
        
        # 移除特殊字符（保留中文、英文、数字和基本标点）
        if language == "zh":
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9.,!?;:，。！？；：]', ' ', text)
        else:
            text = re.sub(r'[^a-zA-Z0-9.,!?;:]', ' ', text)
        
        # 再次移除多余空格
        text = " ".join(text.split())
        
        return text
    
    @staticmethod
    def tokenize(text: str, language: str = "zh") -> List[str]:
        """
        文本分词
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            
        Returns:
            分词列表
        """
        if not text:
            return []
        
        if language == "zh":
            # 中文分词
            return list(jieba.cut(text))
        else:
            # 英文分词
            return word_tokenize(text)
    
    @staticmethod
    def remove_stopwords(tokens: List[str], language: str = "zh") -> List[str]:
        """
        移除停用词
        
        Args:
            tokens: 分词列表
            language: 语言代码，'zh'为中文，'en'为英文
            
        Returns:
            移除停用词后的分词列表
        """
        if not tokens:
            return []
        
        if language == "zh":
            return [token for token in tokens if token not in stop_words_zh]
        else:
            return [token for token in tokens if token.lower() not in stop_words_en]
    
    @staticmethod
    def extract_entities(text: str, language: str = "zh") -> Dict[str, List[str]]:
        """
        实体识别
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            
        Returns:
            实体字典，包含人物、组织、地点等
        """
        entities = {
            "person": [],
            "organization": [],
            "location": [],
            "time": [],
            "other": []
        }
        
        if not text or (nlp_zh is None and nlp_en is None):
            return entities
        
        try:
            # 选择语言模型
            nlp = nlp_zh if language == "zh" else nlp_en
            if nlp is None:
                return entities
            
            # 处理文本
            doc = nlp(text)
            
            # 提取实体
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "PER"]:
                    entities["person"].append(ent.text)
                elif ent.label_ in ["ORG", "ORGANIZATION"]:
                    entities["organization"].append(ent.text)
                elif ent.label_ in ["GPE", "LOC", "LOCATION"]:
                    entities["location"].append(ent.text)
                elif ent.label_ in ["DATE", "TIME"]:
                    entities["time"].append(ent.text)
                else:
                    entities["other"].append(ent.text)
            
            # 去重
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            return entities
        except Exception as e:
            logger.error(f"实体识别出错: {e}")
            return entities
    
    @staticmethod
    def extract_keywords(text: str, language: str = "zh", top_n: int = 10) -> List[str]:
        """
        关键词提取
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 清洗文本
        clean_text = TextProcessor.clean_text(text, language)
        
        # 分词
        tokens = TextProcessor.tokenize(clean_text, language)
        
        # 移除停用词
        tokens = TextProcessor.remove_stopwords(tokens, language)
        
        # 统计词频
        word_freq = {}
        for token in tokens:
            if len(token) > 1:  # 忽略单字符词
                word_freq[token] = word_freq.get(token, 0) + 1
        
        # 排序并返回前N个关键词
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in keywords[:top_n]]
    
    @staticmethod
    def generate_summary(text: str, language: str = "zh", max_sentences: int = 3) -> str:
        """
        生成摘要（简单实现，基于句子重要性）
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            max_sentences: 最大句子数量
            
        Returns:
            摘要文本
        """
        if not text:
            return ""
        
        # 分句
        if language == "zh":
            sentences = re.split(r'[。！？]', text)
        else:
            sentences = re.split(r'[.!?]', text)
        
        # 过滤空句
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # 简单实现：取前N句作为摘要
        summary = sentences[:max_sentences]
        
        # 根据语言添加适当的句尾标点
        if language == "zh":
            return "。".join(summary) + "。"
        else:
            return ". ".join(summary) + "."
    
    @staticmethod
    def analyze_sentiment(text: str, language: str = "zh") -> Dict[str, Any]:
        """
        情感分析（简单实现）
        
        Args:
            text: 原始文本
            language: 语言代码，'zh'为中文，'en'为英文
            
        Returns:
            情感分析结果
        """
        # 这里是一个非常简化的实现
        # 实际应用中应该使用更复杂的情感分析模型
        
        # 正面词汇
        positive_words_zh = {"好", "优秀", "喜欢", "赞", "棒", "强", "满意", "开心", "快乐", "成功"}
        positive_words_en = {"good", "great", "excellent", "like", "love", "best", "nice", "happy", "success", "wonderful"}
        
        # 负面词汇
        negative_words_zh = {"差", "糟糕", "不好", "讨厌", "失败", "弱", "不满", "难过", "痛苦", "问题"}
        negative_words_en = {"bad", "worst", "terrible", "hate", "dislike", "poor", "fail", "sad", "problem", "difficult"}
        
        # 分词
        tokens = TextProcessor.tokenize(text, language)
        
        # 计数
        positive_count = 0
        negative_count = 0
        
        if language == "zh":
            for token in tokens:
                if token in positive_words_zh:
                    positive_count += 1
                elif token in negative_words_zh:
                    negative_count += 1
        else:
            for token in tokens:
                token_lower = token.lower()
                if token_lower in positive_words_en:
                    positive_count += 1
                elif token_lower in negative_words_en:
                    negative_count += 1
        
        # 计算情感得分 (-1 到 1)
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total
        
        # 确定情感标签
        if sentiment_score > 0.2:
            sentiment = "positive"
        elif sentiment_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "positive_count": positive_count,
            "negative_count": negative_count
        } 