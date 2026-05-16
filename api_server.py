#!/usr/bin/env python3
"""
AI Agent 修复工具 API 服务器
提供RESTful API供Web界面调用
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

from aiohttp import web
import aiohttp_cors

# 导入修复引擎
from repair_engine import AIAgentRepairTool, RepairType


class RepairAPIServer:
    """API服务器类"""
    
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.tool = AIAgentRepairTool()
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
    
    def setup_cors(self):
        """配置CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 为所有路由添加CORS
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/api/agents', self.get_agents)
        self.app.router.add_get('/api/agents/{agent_id}/status', self.get_agent_status)
        self.app.router.add_post('/api/agents/{agent_id}/scan', self.scan_agent)
        self.app.router.add_post('/api/agents/{agent_id}/repair', self.repair_agent)
        self.app.router.add_post('/api/agents/{agent_id}/backup', self.backup_agent)
        
        self.app.router.add_get('/api/backups', self.list_backups)
        self.app.router.add_post('/api/backups/{backup_name}/restore', self.restore_backup)
        self.app.router.add_delete('/api/backups/{backup_name}', self.delete_backup)
        
        self.app.router.add_post('/api/batch/repair', self.batch_repair)
        self.app.router.add_post('/api/batch/backup', self.batch_backup)
        
        self.app.router.add_get('/api/system/info', self.get_system_info)
        self.app.router.add_get('/api/repair/report', self.get_repair_report)
        
        # 静态文件服务
        self.app.router.add_static('/', path=Path(__file__).parent, show_index=True)
    
    async def get_agents(self, request):
        """获取所有Agent列表"""
        try:
            agents = []
            for agent_id in self.tool.AGENT_CONFIGS.keys():
                info = self.tool.scan_agent(agent_id)
                agents.append({
                    'id': info.id,
                    'name': info.name,
                    'status': info.status.value,
                    'install_path': str(info.install_path) if info.install_path else None,
                    'version': info.version,
                    'issues': info.issues
                })
            
            return web.json_response({
                'success': True,
                'data': agents
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_agent_status(self, request):
        """获取指定Agent状态"""
        agent_id = request.match_info['agent_id']
        
        try:
            info = self.tool.scan_agent(agent_id)
            return web.json_response({
                'success': True,
                'data': {
                    'id': info.id,
                    'name': info.name,
                    'status': info.status.value,
                    'install_path': str(info.install_path) if info.install_path else None,
                    'config_path': str(info.config_path) if info.config_path else None,
                    'version': info.version,
                    'last_check': info.last_check,
                    'issues': info.issues
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def scan_agent(self, request):
        """扫描指定Agent"""
        agent_id = request.match_info['agent_id']
        
        try:
            info = self.tool.scan_agent(agent_id)
            return web.json_response({
                'success': True,
                'data': {
                    'id': info.id,
                    'name': info.name,
                    'status': info.status.value,
                    'issues': info.issues,
                    'timestamp': info.last_check
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def repair_agent(self, request):
        """修复指定Agent"""
        agent_id = request.match_info['agent_id']
        
        try:
            # 解析请求体
            data = await request.json()
            repair_types = data.get('types', ['config', 'cache', 'plugins'])
            create_backup = data.get('backup', True)
            
            # 转换修复类型
            type_mapping = {
                'config': RepairType.CONFIG,
                'cache': RepairType.CACHE,
                'plugins': RepairType.PLUGINS,
                'data': RepairType.DATA,
                'dependencies': RepairType.DEPS
            }
            
            repair_type_enums = []
            for t in repair_types:
                if t in type_mapping:
                    repair_type_enums.append(type_mapping[t])
            
            # 执行修复
            results = self.tool.full_repair(agent_id, repair_type_enums)
            
            return web.json_response({
                'success': True,
                'data': {
                    'agent_id': agent_id,
                    'results': [asdict(r) for r in results],
                    'backup_created': create_backup
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def backup_agent(self, request):
        """备份指定Agent"""
        agent_id = request.match_info['agent_id']
        
        try:
            data = await request.json() if request.can_read_body else {}
            backup_name = data.get('name')
            
            success, message = self.tool.create_backup(agent_id, backup_name)
            
            return web.json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def list_backups(self, request):
        """列出所有备份"""
        try:
            backups = self.tool.list_backups()
            return web.json_response({
                'success': True,
                'data': backups
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def restore_backup(self, request):
        """从备份恢复"""
        backup_name = request.match_info['backup_name']
        
        try:
            success, message = self.tool.restore_backup(backup_name)
            return web.json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def delete_backup(self, request):
        """删除备份"""
        backup_name = request.match_info['backup_name']
        
        try:
            backup_path = self.tool.backup_dir / backup_name
            if backup_path.exists():
                import shutil
                shutil.rmtree(backup_path)
                return web.json_response({
                    'success': True,
                    'message': f'备份 {backup_name} 已删除'
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': '备份不存在'
                }, status=404)
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def batch_repair(self, request):
        """批量修复"""
        try:
            data = await request.json()
            agent_ids = data.get('agents', [])
            repair_types = data.get('types', ['config', 'cache', 'plugins'])
            
            results = []
            for agent_id in agent_ids:
                agent_results = self.tool.full_repair(agent_id, repair_types)
                results.extend([asdict(r) for r in agent_results])
            
            return web.json_response({
                'success': True,
                'data': {
                    'total_agents': len(agent_ids),
                    'total_repairs': len(results),
                    'results': results
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def batch_backup(self, request):
        """批量备份"""
        try:
            data = await request.json()
            agent_ids = data.get('agents', [])
            
            results = []
            for agent_id in agent_ids:
                success, message = self.tool.create_backup(agent_id)
                results.append({
                    'agent_id': agent_id,
                    'success': success,
                    'message': message
                })
            
            return web.json_response({
                'success': True,
                'data': {
                    'total': len(agent_ids),
                    'results': results
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_system_info(self, request):
        """获取系统信息"""
        import platform
        
        try:
            return web.json_response({
                'success': True,
                'data': {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version(),
                    'backup_dir': str(self.tool.backup_dir)
                }
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_repair_report(self, request):
        """获取修复报告"""
        try:
            report = self.tool.generate_report()
            return web.json_response({
                'success': True,
                'data': report
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def run(self):
        """启动服务器"""
        print(f"=" * 60)
        print("AI Agent 智能修复工具 API 服务器")
        print(f"=" * 60)
        print(f"服务器地址: http://{self.host}:{self.port}")
        print(f"Web界面: http://{self.host}:{self.port}/index.html")
        print(f"备份目录: {self.tool.backup_dir}")
        print(f"=" * 60)
        print("按 Ctrl+C 停止服务器")
        print()
        
        web.run_app(self.app, host=self.host, port=self.port)


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Agent 修复工具 API 服务器')
    parser.add_argument('--host', default='localhost', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口')
    parser.add_argument('--backup-dir', help='备份目录路径')
    
    args = parser.parse_args()
    
    if args.backup_dir:
        os.environ['AI_AGENT_BACKUP_DIR'] = args.backup_dir
    
    server = RepairAPIServer(host=args.host, port=args.port)
    server.run()


if __name__ == '__main__':
    main()
