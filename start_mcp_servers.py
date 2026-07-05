#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
start_mcp_servers.py -- Launch and test all 3 MCP servers.

Usage:
    python start_mcp_servers.py            # List servers
    python start_mcp_servers.py --test     # Smoke-test all servers
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MCP_DIR = os.path.join(ROOT, "mcp")
PYTHON = sys.executable

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SERVERS = [
    {
        "name": "Drug Service",
        "script": os.path.join(MCP_DIR, "drug_server.py"),
        "port": 8001,
        "description": "Drug info, interactions, allergy alerts, dosage guidance",
    },
    {
        "name": "Patient Service",
        "script": os.path.join(MCP_DIR, "patient_server.py"),
        "port": 8002,
        "description": "Patient summaries, risk history, lab results",
    },
    {
        "name": "Guideline Service",
        "script": os.path.join(MCP_DIR, "guideline_server.py"),
        "port": 8003,
        "description": "Clinical guidelines, risk calculators, treatment targets",
    },
]


def _run_mcp_commands(server: dict, commands: list[dict]) -> list[str]:
    """Run a sequence of commands on a single server process session and return their stdout lines."""
    proc = subprocess.Popen(
        [PYTHON, server["script"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,  # Avoid deadlock by discarding stderr
        text=True,
        encoding="utf-8",
        cwd=ROOT,
    )
    
    responses = []
    try:
        for cmd in commands:
            request_line = json.dumps(cmd) + "\n"
            proc.stdin.write(request_line)
            proc.stdin.flush()
            
            # Read one response line
            line = proc.stdout.readline()
            responses.append(line.strip())
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            pass
            
    return responses


def smoke_test_server(server: dict) -> bool:
    init_cmd = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smoke-test-client", "version": "1.0.0"},
        },
    }
    list_cmd = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    
    try:
        responses = _run_mcp_commands(server, [init_cmd, list_cmd])
        if len(responses) < 2:
            print(f"    [FAIL] {server['name']}: Insufficient responses from server")
            return False
            
        init_resp = json.loads(responses[0])
        list_resp = json.loads(responses[1])
        
        if "error" in init_resp:
            print(f"    [FAIL] {server['name']}: Initialization error: {init_resp['error']}")
            return False
            
        if "error" in list_resp:
            print(f"    [FAIL] {server['name']}: list_tools error: {list_resp['error']}")
            return False
            
        tools = list_resp.get("result", {}).get("tools", [])
        tool_names = [t.get("name", "?") for t in tools]
        print(f"    [OK] {server['name']}: {len(tools)} tools -> {', '.join(tool_names)}")
        return True
    except subprocess.TimeoutExpired:
        print(f"    [FAIL] {server['name']}: Timeout")
        return False
    except Exception as e:
        print(f"    [FAIL] {server['name']}: {e}")
        return False


def test_tool_call(server: dict, tool_name: str, args: dict) -> bool:
    init_cmd = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smoke-test-client", "version": "1.0.0"},
        },
    }
    call_cmd = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args},
    }
    
    try:
        responses = _run_mcp_commands(server, [init_cmd, call_cmd])
        if len(responses) < 2:
            print(f"    [FAIL] {tool_name}: Insufficient responses from server")
            return False
            
        call_resp = json.loads(responses[1])
        if "error" in call_resp:
            print(f"    [FAIL] {tool_name}: Error in response: {call_resp['error']}")
            return False
            
        result = call_resp.get("result", {})
        content = result.get("content", [{}])
        text = content[0].get("text", "")[:150] if content else "(no content)"
        first_arg = str(list(args.values())[0])[:30]
        print(f"    [OK] {tool_name}({first_arg}): {text[:100]}...")
        return True
    except Exception as e:
        print(f"    [FAIL] {tool_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("--test", action="store_true", help="Run smoke tests on all servers")
    args = parser.parse_args()

    print("=" * 65)
    print("  MedTwin AI - MCP Server Suite")
    print("=" * 65)
    print()

    if args.test:
        print("Running smoke tests ...\n")
        all_ok = True
        for i, server in enumerate(SERVERS, 1):
            print(f"[{i}/3] {server['name']} -- {server['description']}")
            ok = smoke_test_server(server)
            if not ok:
                all_ok = False
        print()

        print("Running tool-level tests ...\n")
        drug_srv = SERVERS[0]
        guideline_srv = SERVERS[2]

        print("[Drug Server]")
        test_tool_call(drug_srv, "get_drug_info", {"drug_name": "metformin"})
        test_tool_call(drug_srv, "check_drug_interaction", {"drug_a": "metformin", "drug_b": "empagliflozin"})
        test_tool_call(drug_srv, "check_allergy_alert", {"drug_name": "aspirin", "patient_allergies": ["Penicillin"]})
        test_tool_call(drug_srv, "get_dosage_guidance", {"drug_name": "metformin", "indication": "T2DM", "egfr": 35.0, "age": 68})

        print("\n[Guideline Server]")
        test_tool_call(guideline_srv, "search_guidelines", {"query": "diabetes hypertension treatment"})
        test_tool_call(guideline_srv, "get_risk_calculator", {
            "calculator": "ascvd", "age": 62, "gender": "male",
            "systolic_bp": 145.0, "total_cholesterol_mgdl": 220.0,
            "hdl_cholesterol_mgdl": 38.0, "has_diabetes": True, "smoker": False,
        })
        test_tool_call(guideline_srv, "get_treatment_targets", {"condition": "diabetes"})
        test_tool_call(guideline_srv, "get_screening_schedule", {"condition": "diabetes"})
        test_tool_call(guideline_srv, "get_clinical_evidence", {"drug_or_intervention": "empagliflozin"})

        print()
        status = "ALL PASSED" if all_ok else "SOME FAILED"
        print(f"[{status}] MCP smoke tests complete.")

    else:
        print("MCP servers operate in stdio mode (launched per-call by MCPClient).")
        print("Run with --test to verify all tools.\n")
        print("Available MCP Servers:")
        for s in SERVERS:
            print(f"  [MCP] {s['name']:<25}  {s['description']}")
            print(f"        {s['script']}")
        print()
        print("Usage: python start_mcp_servers.py --test")


if __name__ == "__main__":
    main()
