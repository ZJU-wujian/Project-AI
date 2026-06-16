"""翻译 API：支持中英文互译"""
import urllib.request
import urllib.parse
import json
import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/translate", tags=["Translation"])

# 简单内存缓存，避免重复请求同一文本
_translation_cache: Dict[str, str] = {}
_CACHE_TTL = 60 * 60 * 24 * 7  # 7 天
_cache_times: Dict[str, float] = {}


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    source_lang: Optional[str] = Field("auto", description="源语言: auto, zh, en")
    target_lang: str = Field(..., description="目标语言: zh 或 en")


class TranslateResponse(BaseModel):
    original: str
    translated: str
    source_lang: str
    target_lang: str


def _cache_key(text: str, target: str) -> str:
    return hashlib.md5((text + "|" + target).encode("utf-8")).hexdigest()


def _translate_with_mymemory(text: str, target_lang: str) -> str:
    """使用 MyMemory 免费翻译 API"""
    if target_lang == "zh":
        lang_pair = "en|zh-CN"
    else:
        lang_pair = "zh-CN|en"
    params = {
        "q": text[:500],  # MyMemory 单次约 500 字符
        "langpair": lang_pair
    }
    url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated != text:
            return translated
    except Exception:
        pass
    return ""


def _translate_text(text: str, target_lang: str) -> str:
    """翻译核心逻辑：分段处理长文本 + 缓存"""
    if not text or not text.strip():
        return text
    
    normalized_target = "zh" if target_lang.lower() in ["zh", "zh-cn", "zh-tw", "chinese"] else "en"
    
    # 检查缓存
    key = _cache_key(text, normalized_target)
    if key in _translation_cache and time.time() - _cache_times.get(key, 0) < _CACHE_TTL:
        return _translation_cache[key]
    
    # 分段翻译（每段约 400-500 字符，按句号或逗号切）
    segments = _split_text(text, max_len=400)
    translated_segments = []
    
    for seg in segments:
        if not seg.strip() or seg.strip() in ",.;!?。，；！？":
            translated_segments.append(seg)
            continue
        
        result = _translate_with_mymemory(seg, normalized_target)
        if result:
            translated_segments.append(result)
        else:
            translated_segments.append(seg)  # 失败则保留原文
    
    translated = " ".join(translated_segments)
    
    # 写入缓存
    _translation_cache[key] = translated
    _cache_times[key] = time.time()
    
    return translated


def _split_text(text: str, max_len: int = 400) -> List[str]:
    """按句子切分长文本"""
    if len(text) <= max_len:
        return [text]
    
    # 按中英文句号/分号等切分
    import re
    sentences = re.split(r'([.!?。！？；;])', text)
    # 把分隔符粘回前一句
    result = []
    current = ""
    for s in sentences:
        if s in ".!?。！？；;":
            current += s
            if current:
                result.append(current)
            current = ""
        else:
            current += s
    
    if current.strip():
        result.append(current)
    
    # 如果某句仍过长，按逗号再切
    final = []
    for r in result:
        if len(r) <= max_len:
            final.append(r)
        else:
            sub = re.split(r'([,，])', r)
            cur = ""
            for s2 in sub:
                if s2 in ",，":
                    cur += s2
                else:
                    cur += s2
                if len(cur) >= max_len:
                    final.append(cur)
                    cur = ""
            if cur:
                final.append(cur)
    
    return final


@router.post("", response_model=TranslateResponse)
@router.post("/", response_model=TranslateResponse)
def translate_text(req: TranslateRequest):
    """翻译文本：title / abstract（作者名不要翻译，使用时排除 authors 字段）"""
    try:
        translated = _translate_text(req.text, req.target_lang)
        return TranslateResponse(
            original=req.text,
            translated=translated,
            source_lang=req.source_lang,
            target_lang=req.target_lang
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译服务暂不可用: {str(e)}")


@router.post("/batch", response_model=List[TranslateResponse])
def translate_batch(requests: List[TranslateRequest]):
    """批量翻译：用于同时翻译标题和摘要"""
    results = []
    for req in requests[:20]:  # 限制单次最多 20 条
        try:
            translated = _translate_text(req.text, req.target_lang)
            results.append(TranslateResponse(
                original=req.text,
                translated=translated,
                source_lang=req.source_lang,
                target_lang=req.target_lang
            ))
        except Exception:
            results.append(TranslateResponse(
                original=req.text,
                translated=req.text,
                source_lang=req.source_lang,
                target_lang=req.target_lang
            ))
    return results
