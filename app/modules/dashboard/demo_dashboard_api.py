"""
Dashboard API Demo Script

Script này demonstrate tất cả các API endpoints của Dashboard module
với các use cases thực tế và examples.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any


class DashboardAPIDemo:
    """Demo class for Dashboard APIs"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.auth_token = "your_auth_token_here"
        
    async def demo_overview_stats(self):
        """Demo overview statistics API"""
        print("=" * 60)
        print("DEMO: Overview Statistics")
        print("=" * 60)
        
        # Basic overview
        endpoint = f"{self.base_url}/dashboard/overview"
        print(f"GET {endpoint}")
        
        # With date range
        start_date = datetime.now() - timedelta(days=30)
        endpoint_with_params = f"{endpoint}?start_date={start_date.isoformat()}"
        print(f"GET {endpoint_with_params}")
        
        expected_response = {
            "error_code": 0,
            "message": "Lấy thống kê tổng quan thành công",
            "data": {
                "total_users": 1250,
                "active_users_today": 45,
                "active_users_this_week": 320,
                "active_users_this_month": 890,
                "total_conversations": 3420,
                "total_messages": 28500,
                "conversations_today": 12,
                "messages_today": 156,
                "total_revenue": 125000.50,
                "revenue_this_month": 15200.00,
                "revenue_this_week": 3400.00,
                "revenue_today": 450.00,
                "total_files": 2100,
                "total_file_size": 5368709120,  # 5GB in bytes
                "files_uploaded_today": 8,
                "total_question_sessions": 456,
                "completed_sessions": 389,
                "active_sessions": 67
            }
        }
        
        print("Expected Response:")
        print(json.dumps(expected_response, indent=2))
        print()
    
    async def demo_user_analytics(self):
        """Demo user analytics APIs"""
        print("=" * 60)
        print("DEMO: User Analytics")
        print("=" * 60)
        
        # User analytics with pagination
        endpoint = f"{self.base_url}/dashboard/users"
        print(f"GET {endpoint}?page=1&page_size=10&order_by=create_date&order_direction=desc")
        
        expected_response = {
            "error_code": 0,
            "message": "Lấy thống kê người dùng thành công",
            "data": {
                "user_stats": [
                    {
                        "user_id": "usr_001",
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "role": "USER",
                        "rank": "PRO",
                        "total_conversations": 25,
                        "total_messages": 340,
                        "total_files": 12,
                        "last_activity": "2024-01-15T10:30:00Z",
                        "join_date": "2024-01-01T08:00:00Z"
                    }
                ],
                "total_count": 1250,
                "page": 1,
                "page_size": 10
            }
        }
        
        print("Expected Response:")
        print(json.dumps(expected_response, indent=2))
        print()
        
        # User growth stats
        growth_endpoint = f"{self.base_url}/dashboard/users/growth"
        print(f"GET {growth_endpoint}")
        
        growth_response = {
            "error_code": 0,
            "message": "Lấy thống kê tăng trưởng người dùng thành công",
            "data": {
                "daily_growth": [
                    {"date": "2024-01-01", "count": 15},
                    {"date": "2024-01-02", "count": 23},
                    {"date": "2024-01-03", "count": 18}
                ],
                "monthly_growth": [
                    {"year": 2024, "month": 1, "count": 120},
                    {"year": 2024, "month": 2, "count": 145}
                ],
                "role_distribution": {
                    "USER": 1100,
                    "MANAGER": 25,
                    "ADMIN": 5
                },
                "rank_distribution": {
                    "BASIC": 800,
                    "PRO": 350,
                    "ULTRA": 100
                }
            }
        }
        
        print("Expected Response:")
        print(json.dumps(growth_response, indent=2))
        print()
    
    async def demo_revenue_analytics(self):
        """Demo revenue analytics API"""
        print("=" * 60)
        print("DEMO: Revenue Analytics")
        print("=" * 60)
        
        endpoint = f"{self.base_url}/dashboard/revenue"
        print(f"GET {endpoint}")
        
        expected_response = {
            "error_code": 0,
            "message": "Lấy thống kê doanh thu thành công",
            "data": {
                "daily_revenue": [
                    {
                        "date": "2024-01-01",
                        "amount": 1250.00,
                        "transaction_count": 5,
                        "rank_type": None
                    }
                ],
                "monthly_revenue": [
                    {
                        "date": "2024-01",
                        "amount": 45200.00,
                        "transaction_count": 156,
                        "rank_type": None
                    }
                ],
                "revenue_by_rank": {
                    "BASIC": 15200.00,
                    "PRO": 28400.00,
                    "ULTRA": 81600.00
                },
                "total_revenue": 125200.00,
                "average_transaction_value": 803.85
            }
        }
        
        print("Expected Response:")
        print(json.dumps(expected_response, indent=2))
        print()
    
    async def demo_chat_analytics(self):
        """Demo chat analytics APIs"""
        print("=" * 60)
        print("DEMO: Chat Analytics")
        print("=" * 60)
        
        # Chat analytics
        endpoint = f"{self.base_url}/dashboard/chat"
        print(f"GET {endpoint}?page=1&page_size=5")
        
        expected_response = {
            "error_code": 0,
            "message": "Lấy thống kê chat thành công",
            "data": {
                "conversations": [
                    {
                        "conversation_id": "conv_001",
                        "name": "CV Analysis Discussion",
                        "user_name": "Alice Johnson",
                        "user_email": "alice@example.com",
                        "message_count": 45,
                        "file_count": 3,
                        "last_activity": "2024-01-15T14:30:00Z",
                        "created_date": "2024-01-10T09:00:00Z"
                    }
                ],
                "total_conversations": 3420,
                "total_messages": 28500,
                "average_messages_per_conversation": 8.33,
                "most_active_conversations": [],
                "recent_conversations": []
            }
        }
        
        print("Expected Response:")
        print(json.dumps(expected_response, indent=2))
        print()
        
        # Chat usage stats
        usage_endpoint = f"{self.base_url}/dashboard/chat/usage"
        print(f"GET {usage_endpoint}")
        
        usage_response = {
            "error_code": 0,
            "message": "Lấy thống kê sử dụng chat thành công",
            "data": {
                "daily_stats": [
                    {
                        "date": "2024-01-01",
                        "conversations": 25,
                        "messages": 340
                    }
                ],
                "hourly_distribution": [
                    {"hour": 9, "message_count": 120},
                    {"hour": 10, "message_count": 156},
                    {"hour": 14, "message_count": 189}
                ],
                "user_engagement": {
                    "avg_messages_per_conversation": 8.33,
                    "max_messages_in_conversation": 89,
                    "active_users": 234
                }
            }
        }
        
        print("Expected Response:")
        print(json.dumps(usage_response, indent=2))
        print()
    
    async def demo_advanced_reports(self):
        """Demo advanced reporting APIs"""
        print("=" * 60)
        print("DEMO: Advanced Reports")
        print("=" * 60)
        
        # User engagement report
        engagement_endpoint = f"{self.base_url}/dashboard/reports/user-engagement"
        print(f"GET {engagement_endpoint}")
        
        engagement_response = {
            "error_code": 0,
            "message": "Lấy báo cáo user engagement thành công",
            "data": {
                "total_active_users": 890,
                "avg_sessions_per_user": 12.5,
                "avg_session_duration_minutes": 25.3,
                "feature_usage": {
                    "chat": {"users": 850, "adoption_rate": 95.5},
                    "file_upload": {"users": 420, "adoption_rate": 47.2},
                    "surveys": {"users": 234, "adoption_rate": 26.3}
                },
                "retention_rate": {
                    "daily": 85.2,
                    "weekly": 72.8,
                    "monthly": 68.5
                },
                "churn_risk": {
                    "high_risk": 45,
                    "medium_risk": 123,
                    "low_risk": 722
                }
            }
        }
        
        print("Expected Response:")
        print(json.dumps(engagement_response, indent=2))
        print()
        
        # AI Performance report
        ai_endpoint = f"{self.base_url}/dashboard/reports/ai-performance"
        print(f"GET {ai_endpoint}")
        
        ai_response = {
            "error_code": 0,
            "message": "Lấy báo cáo AI performance thành công",
            "data": {
                "usage_metrics": {
                    "total_requests": 25600,
                    "total_tokens": 2340000,
                    "avg_tokens_per_request": 91.4,
                    "estimated_costs": 485.30
                },
                "performance_metrics": {
                    "avg_response_time_ms": 1250.5,
                    "success_rate": 98.7,
                    "error_rate": 1.3,
                    "timeout_rate": 0.2
                },
                "quality_metrics": {
                    "user_ratings": {"1": 12, "2": 45, "3": 234, "4": 567, "5": 890},
                    "avg_rating": 4.2,
                    "response_relevance": 87.3
                }
            }
        }
        
        print("Expected Response:")
        print(json.dumps(ai_response, indent=2))
        print()
    
    async def demo_export_functionality(self):
        """Demo data export functionality"""
        print("=" * 60)
        print("DEMO: Data Export")
        print("=" * 60)
        
        # Create export request
        export_endpoint = f"{self.base_url}/dashboard/reports/export"
        print(f"POST {export_endpoint}")
        
        request_body = {
            "export_type": "xlsx",
            "data_types": ["users", "revenue", "chat"],
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "email": "admin@example.com"
        }
        
        print("Request Body:")
        print(json.dumps(request_body, indent=2))
        
        export_response = {
            "error_code": 0,
            "message": "Export request đã được tạo thành công",
            "data": {
                "task_id": "export_20240115_143022",
                "status": "processing",
                "estimated_completion": "5-10 minutes",
                "download_url": None,
                "will_email": True
            }
        }
        
        print("Expected Response:")
        print(json.dumps(export_response, indent=2))
        print()
        
        # Check export status
        task_id = "export_20240115_143022"
        status_endpoint = f"{self.base_url}/dashboard/reports/export/{task_id}/status"
        print(f"GET {status_endpoint}")
        
        status_response = {
            "error_code": 0,
            "message": "Lấy trạng thái export thành công",
            "data": {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "download_url": f"/api/v1/dashboard/reports/download/{task_id}",
                "created_at": "2024-01-15T14:30:22Z",
                "completed_at": "2024-01-15T14:37:15Z",
                "file_size": "2.5 MB",
                "expires_at": "2024-01-22T14:37:15Z"
            }
        }
        
        print("Expected Response:")
        print(json.dumps(status_response, indent=2))
        print()
    
    async def demo_utility_endpoints(self):
        """Demo utility endpoints"""
        print("=" * 60)
        print("DEMO: Utility Endpoints")
        print("=" * 60)
        
        # System health
        health_endpoint = f"{self.base_url}/dashboard/health"
        print(f"GET {health_endpoint}")
        
        health_response = {
            "error_code": 0,
            "message": "Lấy thông tin sức khỏe hệ thống thành công",
            "data": {
                "database_status": "healthy",
                "total_records": {
                    "users": 1250,
                    "conversations": 3420,
                    "messages": 28500,
                    "files": 2100,
                    "payments": 890,
                    "orders": 456,
                    "question_sessions": 234,
                    "agents": 12
                },
                "storage_info": {
                    "total_file_size": 5368709120,
                    "total_files": 2100,
                    "indexed_files": 1987,
                    "indexing_rate": 94.6
                },
                "performance_metrics": {
                    "avg_messages_per_conversation": 8.33,
                    "avg_files_per_user": 1.68,
                    "completion_rate": 85.3
                },
                "last_updated": "2024-01-15T14:45:30Z"
            }
        }
        
        print("Expected Response:")
        print(json.dumps(health_response, indent=2))
        print()
        
        # Cache refresh
        cache_endpoint = f"{self.base_url}/dashboard/cache/refresh"
        print(f"POST {cache_endpoint}")
        
        cache_response = {
            "error_code": 0,
            "message": "Refresh cache thành công",
            "data": {"success": True}
        }
        
        print("Expected Response:")
        print(json.dumps(cache_response, indent=2))
        print()
    
    async def run_all_demos(self):
        """Run all demo functions"""
        print("🚀 DASHBOARD API COMPLETE DEMONSTRATION")
        print("=" * 80)
        print("This demo showcases all Dashboard APIs with realistic examples")
        print("=" * 80)
        print()
        
        await self.demo_overview_stats()
        await self.demo_user_analytics()
        await self.demo_revenue_analytics()
        await self.demo_chat_analytics()
        await self.demo_advanced_reports()
        await self.demo_export_functionality()
        await self.demo_utility_endpoints()
        
        print("=" * 80)
        print("✅ DEMO COMPLETED")
        print("=" * 80)
        print("\nKey Benefits of this Dashboard System:")
        print("• Comprehensive analytics covering ALL application modules")
        print("• Real-time insights with caching for performance")
        print("• Advanced reporting with export capabilities")
        print("• Proper role-based access control")
        print("• Scalable architecture with repository pattern")
        print("• Background processing for heavy operations")
        print("• Data integrity validation and monitoring")
        print("\nFor complete API documentation, see: app/modules/dashboard/README.md")


# Usage example
async def main():
    """Main demo function"""
    demo = DashboardAPIDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())
