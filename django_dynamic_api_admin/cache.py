"""
Redis 缓存管理
"""
import json
import redis
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis 缓存管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self._client = None
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端（延迟连接）"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 16379),
                    db=self.config.get('db', 0),
                    password=self.config.get('password'),
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # 测试连接
                self._client.ping()
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
                self._client = None
        return self._client
    
    def get(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Redis GET 失败: {e}")
        return None
    
    def set(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        if not self.client:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"Redis SET 失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE 失败: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配的缓存"""
        if not self.client:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis CLEAR 失败: {e}")
        return 0
