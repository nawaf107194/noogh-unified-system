#!/usr/bin/env python3
"""
MCP Client for Terminal
تشغيل MCP tools من الـ Terminal مباشرة
"""

import requests
import json
import sys
from typing import Dict, Any, List

BASE_URL = "https://2f64-2a02-cb80-4288-1295-3dee-280e-ed8a-8eb1.ngrok-free.app"


class MCPClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.tools = None

    def discover_tools(self) -> List[Dict[str, Any]]:
        """اكتشاف جميع الأدوات المتاحة"""
        r = requests.get(f"{self.base_url}/mcp/v1/tools", timeout=10)
        r.raise_for_status()
        self.tools = r.json()['tools']
        return self.tools

    def list_tools(self):
        """عرض قائمة الأدوات"""
        if not self.tools:
            self.discover_tools()

        print(f"\n📋 Available MCP Tools ({len(self.tools)}):\n")
        for i, tool in enumerate(self.tools, 1):
            print(f"{i}. {tool['name']}")
            print(f"   {tool['description']}")
            print()

    def call_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """استدعاء أداة معينة"""
        payload = {
            "name": tool_name,
            "arguments": params or {}
        }

        r = requests.post(
            f"{self.base_url}/mcp/v1/tools/call",
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    def interactive(self):
        """وضع تفاعلي"""
        self.list_tools()

        while True:
            print("\n" + "="*50)
            choice = input("\nاختر أداة (رقم أو اسم، q للخروج): ").strip()

            if choice.lower() == 'q':
                break

            # إذا رقم
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.tools):
                    tool = self.tools[idx]
                else:
                    print("❌ رقم غير صحيح")
                    continue
            else:
                # إذا اسم
                tool = next((t for t in self.tools if t['name'] == choice), None)
                if not tool:
                    print("❌ أداة غير موجودة")
                    continue

            print(f"\n🔧 Tool: {tool['name']}")
            print(f"📝 Description: {tool['description']}")

            # جمع المعاملات
            params = {}
            schema = tool.get('inputSchema', {})
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            if properties:
                print("\n📥 Parameters:")
                for param_name, param_info in properties.items():
                    is_required = param_name in required
                    desc = param_info.get('description', '')
                    default = param_info.get('default', '')

                    prompt = f"  {param_name}"
                    if is_required:
                        prompt += " (required)"
                    if desc:
                        prompt += f" - {desc}"
                    if default:
                        prompt += f" [default: {default}]"
                    prompt += ": "

                    value = input(prompt).strip()

                    if value:
                        params[param_name] = value
                    elif default:
                        params[param_name] = default
                    elif is_required:
                        print(f"❌ {param_name} is required!")
                        break

            # تنفيذ
            try:
                print("\n⏳ Executing...")
                result = self.call_tool(tool['name'], params)
                print("\n✅ Result:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    if len(sys.argv) > 1:
        # وضع command line
        client = MCPClient()

        if sys.argv[1] == "list":
            client.list_tools()

        elif sys.argv[1] == "call":
            if len(sys.argv) < 3:
                print("Usage: python mcp_client.py call <tool_name> [param1=value1] [param2=value2]")
                sys.exit(1)

            tool_name = sys.argv[2]
            params = {}

            for arg in sys.argv[3:]:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    params[key] = value

            try:
                result = client.call_tool(tool_name, params)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        else:
            print("Unknown command. Use: list, call, or run without args for interactive mode")

    else:
        # وضع تفاعلي
        client = MCPClient()
        client.interactive()


if __name__ == "__main__":
    main()
