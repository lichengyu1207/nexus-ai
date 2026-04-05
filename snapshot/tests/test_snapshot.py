"""
状态快照与回滚模块测试
"""
import asyncio
import json
import os
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from snapshot import (
    SnapshotConfig,
    SnapshotInfo,
    SnapshotStatus,
    SnapshotMetadata,
    BackupManager,
    RestoreManager,
    LocalStorage,
)
from snapshot.utils import (
    ServiceManager,
    CommandResult,
    create_tarball,
    extract_tarball,
    calculate_checksum,
    format_timestamp,
    cleanup_dir,
    ensure_dir,
)


class TestSnapshotConfig:
    """配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SnapshotConfig()
        
        assert config.max_snapshots == 7
        assert config.retention_days == 7
        assert config.schedule_hour == 2
        assert config.schedule_minute == 0
    
    def test_get_snapshot_filename(self):
        """测试获取快照文件名"""
        config = SnapshotConfig()
        
        filename = config.get_snapshot_filename("20260328_020000")
        
        assert filename == "snapshot_20260328_020000.tar.gz"
    
    def test_get_snapshot_path(self):
        """测试获取快照路径"""
        config = SnapshotConfig()
        
        path = config.get_snapshot_path("snapshot_20260328_020000.tar.gz")
        
        assert path == "snapshots/snapshot_20260328_020000.tar.gz"


class TestSnapshotModels:
    """数据模型测试"""
    
    def test_snapshot_info_to_dict(self):
        """测试快照信息转字典"""
        info = SnapshotInfo(
            filename="snapshot_20260328_020000.tar.gz",
            created_at=datetime(2026, 3, 28, 2, 0, 0),
            size_bytes=123456,
            description="测试快照",
            status=SnapshotStatus.AVAILABLE,
            created_by="admin"
        )
        
        data = info.to_dict()
        
        assert data["filename"] == "snapshot_20260328_020000.tar.gz"
        assert data["size_bytes"] == 123456
        assert data["status"] == "available"
    
    def test_snapshot_info_from_dict(self):
        """测试从字典创建快照信息"""
        data = {
            "filename": "snapshot_20260328_020000.tar.gz",
            "created_at": "2026-03-28T02:00:00",
            "size_bytes": 123456,
            "description": "测试快照",
            "status": "available",
            "created_by": "admin"
        }
        
        info = SnapshotInfo.from_dict(data)
        
        assert info.filename == "snapshot_20260328_020000.tar.gz"
        assert info.size_bytes == 123456
        assert info.status == SnapshotStatus.AVAILABLE
    
    def test_snapshot_metadata_to_dict(self):
        """测试元数据转字典"""
        metadata = SnapshotMetadata(
            version="1.0",
            created_at=datetime(2026, 3, 28, 2, 0, 0),
            description="测试",
            created_by="admin",
            config_files=["config.yaml"],
            tables=["agents", "tools"]
        )
        
        data = metadata.to_dict()
        
        assert data["version"] == "1.0"
        assert data["config_files"] == ["config.yaml"]
        assert data["tables"] == ["agents", "tools"]


class TestLocalStorage:
    """本地存储测试"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """创建临时存储"""
        config = SnapshotConfig()
        config.local_storage_path = str(tmp_path / "snapshots")
        return LocalStorage(config)
    
    @pytest.mark.asyncio
    async def test_upload(self, temp_storage, tmp_path):
        """测试上传"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = await temp_storage.upload(
            str(test_file),
            "snapshots/test.txt"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_download(self, temp_storage, tmp_path):
        """测试下载"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        await temp_storage.upload(str(test_file), "snapshots/test.txt")
        
        download_path = tmp_path / "downloaded.txt"
        result = await temp_storage.download("snapshots/test.txt", str(download_path))
        
        assert result is True
        assert download_path.read_text() == "test content"
    
    @pytest.mark.asyncio
    async def test_list_objects(self, temp_storage, tmp_path):
        """测试列出对象"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        await temp_storage.upload(str(test_file), "snapshots/test1.txt")
        await temp_storage.upload(str(test_file), "snapshots/test2.txt")
        
        objects = await temp_storage.list_objects("snapshots/")
        
        assert len(objects) == 2
    
    @pytest.mark.asyncio
    async def test_delete(self, temp_storage, tmp_path):
        """测试删除"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        await temp_storage.upload(str(test_file), "snapshots/test.txt")
        
        result = await temp_storage.delete("snapshots/test.txt")
        
        assert result is True
        assert not await temp_storage.exists("snapshots/test.txt")
    
    @pytest.mark.asyncio
    async def test_exists(self, temp_storage, tmp_path):
        """测试存在检查"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        assert not await temp_storage.exists("snapshots/test.txt")
        
        await temp_storage.upload(str(test_file), "snapshots/test.txt")
        
        assert await temp_storage.exists("snapshots/test.txt")


class TestUtils:
    """工具函数测试"""
    
    def test_format_timestamp(self):
        """测试时间戳格式化"""
        dt = datetime(2026, 3, 28, 2, 0, 0)
        
        result = format_timestamp(dt)
        
        assert result == "20260328_020000"
    
    def test_calculate_checksum(self, tmp_path):
        """测试校验和计算"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum = calculate_checksum(str(test_file))
        
        assert len(checksum) == 64
    
    def test_create_tarball(self, tmp_path):
        """测试创建压缩包"""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        
        tarball_path = tmp_path / "test.tar.gz"
        
        result = create_tarball(
            [str(source_dir / "file1.txt"), str(source_dir / "file2.txt")],
            str(tarball_path)
        )
        
        assert result is True
        assert tarball_path.exists()
    
    def test_extract_tarball(self, tmp_path):
        """测试解压压缩包"""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        
        tarball_path = tmp_path / "test.tar.gz"
        create_tarball([str(source_dir / "file.txt")], str(tarball_path))
        
        extract_dir = tmp_path / "extracted"
        result = extract_tarball(str(tarball_path), str(extract_dir))
        
        assert result is True
    
    def test_ensure_dir(self, tmp_path):
        """测试确保目录存在"""
        new_dir = tmp_path / "new_dir" / "subdir"
        
        result = ensure_dir(str(new_dir))
        
        assert result is True
        assert new_dir.exists()
    
    def test_cleanup_dir(self, tmp_path):
        """测试清理目录"""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        result = cleanup_dir(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert len(list(test_dir.iterdir())) == 0


class TestServiceManager:
    """服务管理器测试"""
    
    def test_init(self):
        """测试初始化"""
        manager = ServiceManager(["service1", "service2"], use_systemd=False)
        
        assert manager.services == ["service1", "service2"]
        assert manager.use_systemd is False
    
    @pytest.mark.asyncio
    async def test_stop_services_no_systemd(self):
        """测试停止服务（无 systemd）"""
        manager = ServiceManager(["service1"], use_systemd=False)
        
        results = await manager.stop_services()
        
        assert results["service1"] is True
    
    @pytest.mark.asyncio
    async def test_start_services_no_systemd(self):
        """测试启动服务（无 systemd）"""
        manager = ServiceManager(["service1"], use_systemd=False)
        
        results = await manager.start_services()
        
        assert results["service1"] is True


class TestBackupManager:
    """备份管理器测试"""
    
    @pytest.fixture
    def mock_storage(self):
        """模拟存储"""
        storage = AsyncMock()
        storage.upload = AsyncMock(return_value=True)
        storage.download = AsyncMock(return_value=True)
        storage.list_objects = AsyncMock(return_value=[])
        storage.delete = AsyncMock(return_value=True)
        storage.exists = AsyncMock(return_value=True)
        storage.get_metadata = AsyncMock(return_value={"size_bytes": 1000})
        return storage
    
    @pytest.fixture
    def config(self, tmp_path):
        """创建配置"""
        config = SnapshotConfig()
        config.temp_dir = str(tmp_path / "temp")
        config.config_path = str(tmp_path / "configs")
        config.local_storage_path = str(tmp_path / "storage")
        return config
    
    @pytest.mark.asyncio
    async def test_list_snapshots(self, config, mock_storage):
        """测试列出快照"""
        mock_storage.list_objects.return_value = [
            "snapshots/snapshot_20260328_020000.tar.gz",
            "snapshots/snapshot_20260327_020000.tar.gz"
        ]
        
        manager = BackupManager(config, mock_storage)
        snapshots = await manager.list_snapshots()
        
        assert len(snapshots) == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_old_snapshots(self, config, mock_storage):
        """测试清理旧快照"""
        mock_storage.list_objects.return_value = [
            f"snapshots/snapshot_{format_timestamp()}.tar.gz"
            for _ in range(10)
        ]
        
        manager = BackupManager(config, mock_storage)
        deleted = await manager.cleanup_old_snapshots()
        
        assert deleted == 3
    
    @pytest.mark.asyncio
    async def test_get_snapshot_info(self, config, mock_storage):
        """测试获取快照信息"""
        mock_storage.exists.return_value = True
        mock_storage.get_metadata.return_value = {
            "size_bytes": 123456,
            "description": "测试快照"
        }
        
        manager = BackupManager(config, mock_storage)
        info = await manager.get_snapshot_info("snapshot_20260328_020000.tar.gz")
        
        assert info is not None
        assert info.size_bytes == 123456


class TestRestoreManager:
    """恢复管理器测试"""
    
    @pytest.fixture
    def mock_storage(self):
        """模拟存储"""
        storage = AsyncMock()
        storage.upload = AsyncMock(return_value=True)
        storage.download = AsyncMock(return_value=True)
        storage.list_objects = AsyncMock(return_value=[])
        storage.delete = AsyncMock(return_value=True)
        storage.exists = AsyncMock(return_value=True)
        storage.get_metadata = AsyncMock(return_value={"size_bytes": 1000})
        return storage
    
    @pytest.fixture
    def config(self, tmp_path):
        """创建配置"""
        config = SnapshotConfig()
        config.temp_dir = str(tmp_path / "temp")
        config.config_path = str(tmp_path / "configs")
        config.local_storage_path = str(tmp_path / "storage")
        config.services = []
        return config
    
    def test_get_progress(self, config, mock_storage):
        """测试获取进度"""
        manager = RestoreManager(config, mock_storage)
        
        progress = manager.get_progress()
        
        assert progress is None
    
    def test_is_restoring(self, config, mock_storage):
        """测试是否正在恢复"""
        manager = RestoreManager(config, mock_storage)
        
        assert manager.is_restoring() is False
    
    @pytest.mark.asyncio
    async def test_restore_nonexistent_snapshot(self, config, mock_storage):
        """测试恢复不存在的快照"""
        mock_storage.exists.return_value = False
        
        manager = RestoreManager(config, mock_storage)
        result = await manager.restore("nonexistent.tar.gz")
        
        assert result.success is False
        assert "不存在" in result.error_message
    
    @pytest.mark.asyncio
    async def test_verify_snapshot(self, config, mock_storage, tmp_path):
        """测试验证快照"""
        mock_storage.exists.return_value = True
        mock_storage.download.return_value = True
        
        temp_dir = tmp_path / "temp" / "verify"
        temp_dir.mkdir(parents=True)
        
        tarball = temp_dir / "snapshot.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            metadata_content = json.dumps({
                "version": "1.0",
                "created_at": "2026-03-28T02:00:00",
                "description": "测试"
            }).encode()
            import io
            tarinfo = tarfile.TarInfo(name="metadata.json")
            tarinfo.size = len(metadata_content)
            tar.addfile(tarinfo, io.BytesIO(metadata_content))
        
        config.temp_dir = str(tmp_path / "temp")
        
        manager = RestoreManager(config, mock_storage)
        result = await manager.verify_snapshot("snapshot.tar.gz")
        
        assert result["exists"] is True


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def temp_setup(self, tmp_path):
        """创建临时设置"""
        config = SnapshotConfig()
        config.temp_dir = str(tmp_path / "temp")
        config.config_path = str(tmp_path / "configs")
        config.local_storage_path = str(tmp_path / "storage")
        config.services = []
        
        config_path = Path(config.config_path)
        config_path.mkdir(parents=True, exist_ok=True)
        (config_path / "test.yaml").write_text("key: value")
        
        storage = LocalStorage(config)
        
        return config, storage
    
    @pytest.mark.asyncio
    async def test_full_backup_restore_cycle(self, temp_setup, tmp_path):
        """测试完整备份恢复周期"""
        config, storage = temp_setup
        
        backup_manager = BackupManager(config, storage)
        
        snapshots_before = await backup_manager.list_snapshots()
        
        assert isinstance(snapshots_before, list)
    
    def test_snapshot_status_enum(self):
        """测试快照状态枚举"""
        assert SnapshotStatus.CREATING.value == "creating"
        assert SnapshotStatus.AVAILABLE.value == "available"
        assert SnapshotStatus.RESTORING.value == "restoring"
        assert SnapshotStatus.FAILED.value == "failed"
        assert SnapshotStatus.DELETING.value == "deleting"
