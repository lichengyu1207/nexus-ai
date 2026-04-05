"""
工具函数
服务管理、命令执行等
"""
import asyncio
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ServiceManager:
    """服务管理器"""
    
    def __init__(self, services: List[str], use_systemd: bool = True):
        self.services = services
        self.use_systemd = use_systemd
    
    async def stop_services(self) -> Dict[str, bool]:
        """停止所有服务"""
        results = {}
        for service in self.services:
            results[service] = await self._stop_service(service)
        return results
    
    async def start_services(self) -> Dict[str, bool]:
        """启动所有服务"""
        results = {}
        for service in self.services:
            results[service] = await self._start_service(service)
        return results
    
    async def restart_services(self) -> Dict[str, bool]:
        """重启所有服务"""
        results = {}
        for service in self.services:
            results[service] = await self._restart_service(service)
        return results
    
    async def get_service_status(self, service: str) -> str:
        """获取服务状态"""
        try:
            if self.use_systemd:
                result = await run_command(
                    ["systemctl", "is-active", service],
                    check=False
                )
                return result.stdout.strip() if result.returncode == 0 else "inactive"
            else:
                return "unknown"
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return "unknown"
    
    async def _stop_service(self, service: str) -> bool:
        """停止单个服务"""
        try:
            if self.use_systemd:
                result = await run_command(
                    ["systemctl", "stop", service],
                    check=False
                )
                success = result.returncode == 0
                logger.info(f"停止服务 {service}: {'成功' if success else '失败'}")
                return success
            return True
        except Exception as e:
            logger.error(f"停止服务 {service} 失败: {e}")
            return False
    
    async def _start_service(self, service: str) -> bool:
        """启动单个服务"""
        try:
            if self.use_systemd:
                result = await run_command(
                    ["systemctl", "start", service],
                    check=False
                )
                success = result.returncode == 0
                logger.info(f"启动服务 {service}: {'成功' if success else '失败'}")
                return success
            return True
        except Exception as e:
            logger.error(f"启动服务 {service} 失败: {e}")
            return False
    
    async def _restart_service(self, service: str) -> bool:
        """重启单个服务"""
        try:
            if self.use_systemd:
                result = await run_command(
                    ["systemctl", "restart", service],
                    check=False
                )
                success = result.returncode == 0
                logger.info(f"重启服务 {service}: {'成功' if success else '失败'}")
                return success
            return True
        except Exception as e:
            logger.error(f"重启服务 {service} 失败: {e}")
            return False


class CommandResult:
    """命令执行结果"""
    
    def __init__(
        self,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
        command: List[str] = None
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command or []
    
    @property
    def success(self) -> bool:
        return self.returncode == 0


async def run_command(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
    timeout: int = 300
) -> CommandResult:
    """
    异步执行命令
    
    Args:
        command: 命令及参数列表
        cwd: 工作目录
        env: 环境变量
        check: 是否检查返回码
        timeout: 超时时间（秒）
        
    Returns:
        命令执行结果
    """
    logger.debug(f"执行命令: {' '.join(command)}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={**os.environ, **(env or {})}
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        result = CommandResult(
            returncode=process.returncode,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
            command=command
        )
        
        if check and not result.success:
            logger.error(f"命令执行失败: {' '.join(command)}")
            logger.error(f"stderr: {result.stderr}")
            raise subprocess.CalledProcessError(
                result.returncode,
                command,
                result.stdout,
                result.stderr
            )
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"命令执行超时: {' '.join(command)}")
        raise
    except Exception as e:
        logger.error(f"命令执行异常: {e}")
        raise


async def run_pg_dump(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    output_path: str,
    tables: Optional[List[str]] = None,
    format: str = "custom"
) -> bool:
    """
    执行 PostgreSQL 数据库备份
    
    Args:
        host: 数据库主机
        port: 数据库端口
        database: 数据库名
        user: 用户名
        password: 密码
        output_path: 输出文件路径
        tables: 要备份的表列表（可选）
        format: 备份格式（custom/plain）
        
    Returns:
        是否成功
    """
    env = {"PGPASSWORD": password}
    
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
    ]
    
    if format == "custom":
        cmd.extend(["-Fc"])
    elif format == "plain":
        cmd.extend(["-Fp"])
    
    if tables:
        for table in tables:
            cmd.extend(["-t", table])
    
    cmd.extend(["-f", output_path])
    
    try:
        result = await run_command(cmd, env=env, check=False)
        if result.success:
            logger.info(f"数据库备份成功: {output_path}")
            return True
        else:
            logger.error(f"数据库备份失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"数据库备份异常: {e}")
        return False


async def run_pg_restore(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    input_path: str,
    clean: bool = True
) -> bool:
    """
    执行 PostgreSQL 数据库恢复
    
    Args:
        host: 数据库主机
        port: 数据库端口
        database: 数据库名
        user: 用户名
        password: 密码
        input_path: 输入文件路径
        clean: 是否先清理现有数据
        
    Returns:
        是否成功
    """
    env = {"PGPASSWORD": password}
    
    cmd = [
        "pg_restore",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
    ]
    
    if clean:
        cmd.extend(["--clean", "--if-exists"])
    
    cmd.append(input_path)
    
    try:
        result = await run_command(cmd, env=env, check=False)
        if result.success or result.returncode == 1:
            logger.info(f"数据库恢复成功: {input_path}")
            return True
        else:
            logger.error(f"数据库恢复失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"数据库恢复异常: {e}")
        return False


async def drop_and_create_schema(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    schema: str = "public"
) -> bool:
    """
    删除并重建数据库 schema
    
    Args:
        host: 数据库主机
        port: 数据库端口
        database: 数据库名
        user: 用户名
        password: 密码
        schema: schema 名称
        
    Returns:
        是否成功
    """
    env = {"PGPASSWORD": password}
    
    drop_cmd = [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
        "-c", f"DROP SCHEMA IF EXISTS {schema} CASCADE;"
    ]
    
    create_cmd = [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
        "-c", f"CREATE SCHEMA {schema};"
    ]
    
    try:
        drop_result = await run_command(drop_cmd, env=env, check=False)
        if not drop_result.success:
            logger.warning(f"删除 schema 失败: {drop_result.stderr}")
        
        create_result = await run_command(create_cmd, env=env, check=False)
        if create_result.success:
            logger.info(f"重建 schema 成功: {schema}")
            return True
        else:
            logger.error(f"创建 schema 失败: {create_result.stderr}")
            return False
    except Exception as e:
        logger.error(f"重建 schema 异常: {e}")
        return False


def create_tarball(
    source_paths: List[str],
    output_path: str,
    base_dir: Optional[str] = None
) -> bool:
    """
    创建 tar.gz 压缩包
    
    Args:
        source_paths: 源路径列表
        output_path: 输出文件路径
        base_dir: 基础目录（用于相对路径）
        
    Returns:
        是否成功
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with tarfile.open(output_path, "w:gz") as tar:
            for source_path in source_paths:
                path = Path(source_path)
                if path.exists():
                    if base_dir:
                        arcname = os.path.relpath(source_path, base_dir)
                    else:
                        arcname = path.name
                    tar.add(source_path, arcname=arcname)
                    logger.debug(f"添加到压缩包: {source_path} -> {arcname}")
        
        logger.info(f"压缩包创建成功: {output_path}")
        return True
    except Exception as e:
        logger.error(f"创建压缩包失败: {e}")
        return False


def extract_tarball(
    tarball_path: str,
    output_dir: str
) -> bool:
    """
    解压 tar.gz 压缩包
    
    Args:
        tarball_path: 压缩包路径
        output_dir: 输出目录
        
    Returns:
        是否成功
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(output_dir)
        
        logger.info(f"压缩包解压成功: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"解压压缩包失败: {e}")
        return False


def calculate_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    计算文件校验和
    
    Args:
        file_path: 文件路径
        algorithm: 算法（md5/sha256）
        
    Returns:
        校验和
    """
    if algorithm == "md5":
        hasher = hashlib.md5()
    else:
        hasher = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def get_file_size(file_path: str) -> int:
    """获取文件大小"""
    return os.path.getsize(file_path)


def ensure_dir(path: str) -> bool:
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        return False


def cleanup_dir(path: str) -> bool:
    """清理目录"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"清理目录失败: {e}")
        return False


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """格式化时间戳"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """解析时间戳"""
    try:
        return datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
    except ValueError:
        try:
            return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
