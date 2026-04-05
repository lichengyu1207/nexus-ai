# -*- coding: utf-8 -*-
"""
Language Middleware
Extract language preference from request and inject into request.state
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

SUPPORTED_LANGUAGES = ['en', 'zh']
DEFAULT_LANGUAGE = 'en'

class LanguageMiddleware(BaseHTTPMiddleware):
    """
    Language detection middleware
    
    Priority:
    1. URL parameter: ?lang=en
    2. Accept-Language header
    3. Cookie: user_lang
    4. Default: en
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        lang = DEFAULT_LANGUAGE
        
        if 'lang' in request.query_params:
            query_lang = request.query_params.get('lang')
            if query_lang in SUPPORTED_LANGUAGES:
                lang = query_lang
        elif 'accept-language' in request.headers:
            accept_language = request.headers['accept-language']
            lang = self._parse_accept_language(accept_language)
        elif 'user_lang' in request.cookies:
            cookie_lang = request.cookies.get('user_lang')
            if cookie_lang in SUPPORTED_LANGUAGES:
                lang = cookie_lang
        
        request.state.lang = lang
        
        response = await call_next(request)
        
        response.headers['Content-Language'] = lang
        
        return response
    
    def _parse_accept_language(self, accept_language: str) -> str:
        """Parse Accept-Language header"""
        languages = []
        
        for part in accept_language.split(','):
            part = part.strip()
            if ';' in part:
                lang_part, q_part = part.split(';', 1)
                lang = lang_part.strip()
                try:
                    q = float(q_part.strip().split('=')[1])
                except (IndexError, ValueError):
                    q = 1.0
            else:
                lang = part.strip()
                q = 1.0
            
            if '-' in lang:
                lang = lang.split('-')[0]
            
            languages.append((lang, q))
        
        languages.sort(key=lambda x: x[1], reverse=True)
        
        for lang, _ in languages:
            if lang in SUPPORTED_LANGUAGES:
                return lang
        
        return DEFAULT_LANGUAGE


def get_language(request: Request) -> str:
    """Get current language from request state"""
    return getattr(request.state, 'lang', DEFAULT_LANGUAGE)
