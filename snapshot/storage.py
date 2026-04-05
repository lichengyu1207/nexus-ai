"""
对象存储接口
支持本地存储、S3 和阿里云 OSS
"""
import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import SnapshotConfig
from .models import SnapshotInfo, SnapshotStatus

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    async def download(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    async def list_objects(self, prefix: str) -> List[str]:
        """列出对象"""
        pass
    
    @abstractmethod
    async def delete(self, remote_path: str) -> bool:
        """删除对象"""
        pass
    
    @abstractmethod
    async def exists(self, remote_path: str) -> bool:
        """检查对象是否存在"""
        pass
    
    @abstractmethod
    async def get_metadata(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """获取对象元数据"""
        pass


class LocalStorage(StorageBackend):
    """本地文件存储"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.storage_path = Path(config.local_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.storage_path / "snapshots.json"
        self._metadata: Dict[str, Any] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """加载元数据"""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
                self._metadata = {}
    
    def _save_metadata(self) -> None:
        """保存元数据"""
        try:
            with open(self._metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    async def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件（复制到本地存储目录）"""
        try:
            dest_path = self.storage_path / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest_path)
            
            size = os.path.getsize(local_path)
            self._metadata[remote_path] = {
                "filename": os.path.basename(remote_path),
                "size_bytes": size,
                "created_at": datetime.now().isoformat(),
                "status": SnapshotStatus.AVAILABLE.value,
            }
            self._save_metadata()
            
            logger.info(f"文件已上传到本地存储: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False
    
    async def download(self, remote_path: str, local_path: str) -> bool:
        """下载文件（从本地存储目录复制）"""
        try:
            src_path = self.storage_path / remote_path
            if not src_path.exists():
                logger.error(f"文件不存在: {src_path}")
                return False
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            shutil.copy2(src_path, local_path)
            
            logger.info(f"文件已下载到: {local_path}")
            return True
        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False
    
    async def list_objects(self, prefix: str) -> List[str]:
        """列出对象"""
        try:
            objects = []
            for key in self._metadata.keys():
                if key.startswith(prefix):
                    objects.append(key)
            return sorted(objects, reverse=True)
        except Exception as e:
            logger.error(f"列出对象失败: {e}")
            return []
    
    async def delete(self, remote_path: str) -> bool:
        """删除对象"""
        try:
            file_path = self.storage_path / remote_path
            if file_path.exists():
                os.remove(file_path)
            
            if remote_path in self._metadata:
                del self._metadata[remote_path]
                self._save_metadata()
            
            logger.info(f"文件已删除: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """检查对象是否存在"""
        file_path = self.storage_path / remote_path
        return file_path.exists()
    
    async def get_metadata(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """获取对象元数据"""
        return self._metadata.get(remote_path)


class S3Storage(StorageBackend):
    """AWS S3 存储"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.bucket = config.s3_bucket
        self._client: Any = None
    
    def _get_client(self) -> Any:
        """获取 S3 客户端"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    's3',
                    endpoint_url=self.config.s3_endpoint or None,
                    aws_access_key_id=self.config.s3_access_key,
                    aws_secret_access_key=self.config.s3_secret_key,
                    region_name=self.config.s3_region,
                )
            except ImportError:
                raise ImportError("请安装 boto3: pip install boto3")
        return self._client
    
    async def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件到 S3"""
        try:
            client = self._get_client()
            client.upload_file(local_path, self.bucket, remote_path)
            logger.info(f"文件已上传到 S3: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"上传到 S3 失败: {e}")
            return False
    
    async def download(self, remote_path: str, local_path: str) -> bool:
        """从 S3 下载文件"""
        try:
            client = self._get_client()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            client.download_file(self.bucket, remote_path, local_path)
            logger.info(f"文件已从 S3 下载: {local_path}")
            return True
        except Exception as e:
            logger.error(f"从 S3 下载失败: {e}")
            return False
    
    async def list_objects(self, prefix: str) -> List[str]:
        """列出 S3 对象"""
        try:
            client = self._get_client()
            objects = []
            paginator = client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    objects.append(obj['Key'])
            
            return sorted(objects, reverse=True)
        except Exception as e:
            logger.error(f"列出 S3 对象失败: {e}")
            return []
    
    async def delete(self, remote_path: str) -> bool:
        """删除 S3 对象"""
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=remote_path)
            logger.info(f"S3 对象已删除: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"删除 S3 对象失败: {e}")
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """检查 S3 对象是否存在"""
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket, Key=remote_path)
            return True
        except Exception:
            return False
    
    async def get_metadata(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """获取 S3 对象元数据"""
        try:
            client = self._get_client()
            response = client.head_object(Bucket=self.bucket, Key=remote_path)
            return {
                "size_bytes": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag', ''),
            }
        except Exception as e:
            logger.error(f"获取 S3 元数据失败: {e}")
            return None


class OSSStorage(StorageBackend):
    """阿里云 OSS 存储"""
    
    def __init__(self, config: SnapshotConfig):
        self.config = config
        self.bucket_name = config.oss_bucket
        self._bucket: Any = None
    
    def _get_bucket(self) -> Any:
        """获取 OSS Bucket"""
        if self._bucket is None:
            try:
                import oss2
                auth = oss2.Auth(
                    self.config.oss_access_key_id,
                    self.config.oss_access_key_secret
                )
                self._bucket = oss2.Bucket(
                    auth,
                    self.config.oss_endpoint,
                    self.bucket_name
                )
            except ImportError:
                raise ImportError("请安装 oss2: pip install oss2")
        return self._bucket
    
    async def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件到 OSS"""
        try:
            bucket = self._get_bucket()
            bucket.put_object_from_file(remote_path, local_path)
            logger.info(f"文件已上传到 OSS: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"上传到 OSS 失败: {e}")
            return False
    
    async def download(self, remote_path: str, local_path: str) -> bool:
        """从 OSS 下载文件"""
        try:
            bucket = self._get_bucket()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            bucket.get_object_to_file(remote_path, local_path)
            logger.info(f"文件已从 OSS 下载: {local_path}")
            return True
        except Exception as e:
            logger.error(f"从 OSS 下载失败: {e}")
            return False
    
    async def list_objects(self, prefix: str) -> List[str]:
        """列出 OSS 对象"""
        try:
            import oss2
            bucket = self._get_bucket()
            objects = []
            for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                objects.append(obj.key)
            return sorted(objects, reverse=True)
        except Exception as e:
            logger.error(f"列出 OSS 对象失败: {e}")
            return []
    
    async def delete(self, remote_path: str) -> bool:
        """删除 OSS 对象"""
        try:
            bucket = self._get_bucket()
            bucket.delete_object(remote_path)
            logger.info(f"OSS 对象已删除: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"删除 OSS 对象失败: {e}")
            return False
    
    async def exists(self, remote_path: str) -> bool:
        """检查 OSS 对象是否存在"""
        try:
            bucket = self._get_bucket()
            return bucket.object_exists(remote_path)
        except Exception:
            return False
    
    async def get_metadata(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """获取 OSS 对象元数据"""
        try:
            bucket = self._get_bucket()
            info = bucket.head_object(remote_path)
            return {
                "size_bytes": info.content_length,
                "last_modified": info.last_modified,
                "etag": info.etag,
            }
        except Exception as e:
            logger.error(f"获取 OSS 元数据失败: {e}")
            return None


def create_storage_backend(config: SnapshotConfig) -> StorageBackend:
    """创建存储后端"""
    if config.storage_type.value == "local":
        return LocalStorage(config)
    elif config.storage_type.value == "s3":
        return S3Storage(config)
    elif config.storage_type.value == "oss":
        return OSSStorage(config)
    else:
        raise ValueError(f"不支持的存储类型: {config.storage_type}")
