"""
国际化 (i18n) 支持模块
支持多语言切换，自动检测系统语言

Usage:
    from core.i18n import _, set_language, get_language
    
    # 获取翻译
    print(_("scanning_agents"))
    
    # 切换语言
    set_language("en")
    
    # 获取当前语言
    lang = get_language()
"""

import json
import locale
import os
from pathlib import Path
from typing import Dict, Optional

# 默认语言
DEFAULT_LANGUAGE = "en"

# 当前语言
_current_language = None

# 翻译数据存储
_translations: Dict[str, Dict[str, str]] = {}

# 支持的语言列表
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "ko": "한국어",
    "ru": "Русский",
}


def _get_locale_dir() -> Path:
    """获取语言文件目录"""
    return Path(__file__).parent.parent / "locales"


def _load_translations(lang: str) -> Dict[str, str]:
    """加载指定语言的翻译文件"""
    locale_dir = _get_locale_dir()
    file_path = locale_dir / f"{lang}.json"
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {}


def _detect_system_language() -> str:
    """自动检测系统语言"""
    try:
        # 尝试获取系统默认语言
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            lang_code = system_locale.split('_')[0].lower()
            if lang_code in SUPPORTED_LANGUAGES:
                return lang_code
    except:
        pass
    
    # 检查环境变量
    env_lang = os.environ.get('LANG', '') or os.environ.get('LANGUAGE', '')
    if env_lang:
        lang_code = env_lang.split('_')[0].split('.')[0].lower()
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
    
    return DEFAULT_LANGUAGE


def get_language() -> str:
    """获取当前语言代码"""
    global _current_language
    if _current_language is None:
        _current_language = _detect_system_language()
    return _current_language


def set_language(lang: str) -> bool:
    """
    设置当前语言
    
    Args:
        lang: 语言代码 (en, zh, ja, es, etc.)
    
    Returns:
        是否设置成功
    """
    global _current_language
    
    lang = lang.lower()
    if lang not in SUPPORTED_LANGUAGES:
        return False
    
    # 加载翻译数据
    if lang not in _translations:
        translations = _load_translations(lang)
        if translations:
            _translations[lang] = translations
        else:
            return False
    
    _current_language = lang
    return True


def _(key: str, **kwargs) -> str:
    """
    获取翻译文本
    
    Args:
        key: 翻译键名
        **kwargs: 格式化参数
    
    Returns:
        翻译后的文本
    """
    lang = get_language()
    
    # 确保翻译数据已加载
    if lang not in _translations:
        _translations[lang] = _load_translations(lang)
    
    # 获取翻译文本
    text = _translations.get(lang, {}).get(key, key)
    
    # 如果当前语言没有翻译，尝试使用英文
    if text == key and lang != DEFAULT_LANGUAGE:
        if DEFAULT_LANGUAGE not in _translations:
            _translations[DEFAULT_LANGUAGE] = _load_translations(DEFAULT_LANGUAGE)
        text = _translations.get(DEFAULT_LANGUAGE, {}).get(key, key)
    
    # 格式化参数
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def get_available_languages() -> Dict[str, str]:
    """获取所有支持的语言"""
    return SUPPORTED_LANGUAGES.copy()


# 初始化时加载默认语言
set_language(DEFAULT_LANGUAGE)
