#!/usr/bin/env python3
"""
Health Check YAML 生成器
根据服务类型自动生成推荐的 probe 配置
"""

import argparse
from typing import Dict, Any

# 服务类型对应的最佳实践配置
PROBE_TEMPLATES = {
    "java-spring": {
        "name": "Java Spring Boot",
        "readiness": {
            "httpGet": {"path": "/actuator/health/readiness", "port": 8080},
            "initialDelaySeconds": 30,
            "periodSeconds": 10,
            "timeoutSeconds": 5,
            "failureThreshold": 3
        },
        "liveness": {
            "httpGet": {"path": "/actuator/health/liveness", "port": 8080},
            "initialDelaySeconds": 60,
            "periodSeconds": 15,
            "timeoutSeconds": 5,
            "failureThreshold": 3
        },
        "startup": None
    },
    
    "go-http": {
        "name": "Go HTTP Server",
        "readiness": {
            "httpGet": {"path": "/readyz", "port": 8080},
            "initialDelaySeconds": 5,
            "periodSeconds": 5,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "liveness": {
            "httpGet": {"path": "/livez", "port": 8080},
            "initialDelaySeconds": 15,
            "periodSeconds": 10,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "startup": None
    },
    
    "nginx": {
        "name": "Nginx",
        "readiness": {
            "httpGet": {"path": "/health", "port": 80},
            "initialDelaySeconds": 5,
            "periodSeconds": 5,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "liveness": {
            "exec": {"command": ["nginx", "-t"]},
            "initialDelaySeconds": 10,
            "periodSeconds": 30,
            "timeoutSeconds": 5,
            "failureThreshold": 1
        },
        "startup": None
    },
    
    "nodejs": {
        "name": "Node.js Express",
        "readiness": {
            "httpGet": {"path": "/health/ready", "port": 3000},
            "initialDelaySeconds": 10,
            "periodSeconds": 5,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "liveness": {
            "httpGet": {"path": "/health/live", "port": 3000},
            "initialDelaySeconds": 20,
            "periodSeconds": 10,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "startup": None
    },
    
    "python": {
        "name": "Python Flask/FastAPI",
        "readiness": {
            "httpGet": {"path": "/healthz", "port": 8000},
            "initialDelaySeconds": 10,
            "periodSeconds": 5,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "liveness": {
            "httpGet": {"path": "/livez", "port": 8000},
            "initialDelaySeconds": 15,
            "periodSeconds": 10,
            "timeoutSeconds": 2,
            "failureThreshold": 3
        },
        "startup": None
    },
    
    "slow-start": {
        "name": "Slow Starting Application",
        "readiness": None,
        "liveness": {
            "httpGet": {"path": "/health", "port": 8080},
            "initialDelaySeconds": 60,
            "periodSeconds": 15,
            "timeoutSeconds": 5,
            "failureThreshold": 5
        },
        "startup": {
            "httpGet": {"path": "/health", "port": 8080},
            "failureThreshold": 60,  # 60 * 10 = 600s = 10分钟
            "periodSeconds": 10
        }
    },
    
    "database": {
        "name": "Database (PostgreSQL)",
        "readiness": {
            "exec": {"command": ["pg_isready", "-U", "postgres"]},
            "initialDelaySeconds": 10,
            "periodSeconds": 10,
            "timeoutSeconds": 5,
            "failureThreshold": 3
        },
        "liveness": None,  # 数据库不建议 liveness
        "startup": None
    }
}


def generate_deployment_yaml(
    app_name: str,
    app_type: str,
    image: str,
    port: int = 8080
) -> str:
    """生成完整的 Deployment YAML"""
    
    if app_type not in PROBE_TEMPLATES:
        print(f"❌ 不支持的应用类型: {app_type}")
        print(f"支持的类型: {', '.join(PROBE_TEMPLATES.keys())}")
        return ""
    
    template = PROBE_TEMPLATES[app_type]
    
    yaml_parts = [f"""# {app_name} Deployment with Health Check
# Type: {template['name']}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: {port}
"""]
    
    # 添加 readinessProbe
    if template.get('readiness'):
        probe = template['readiness']
        yaml_parts.append("        readinessProbe:")
        yaml_parts.append(generate_probe_yaml(probe, "          "))
    
    # 添加 livenessProbe
    if template.get('liveness'):
        probe = template['liveness']
        yaml_parts.append("        livenessProbe:")
        yaml_parts.append(generate_probe_yaml(probe, "          "))
    
    # 添加 startupProbe
    if template.get('startup'):
        probe = template['startup']
        yaml_parts.append("        startupProbe:")
        yaml_parts.append(generate_probe_yaml(probe, "          "))
    
    yaml_parts.append("""---
apiVersion: v1
kind: Service
metadata:
  name: """ + app_name + """
spec:
  selector:
    app: """ + app_name + """
  ports:
  - port: 80
    targetPort: """ + str(port) + """
  type: ClusterIP
""")
    
    return '\n'.join(yaml_parts)


def generate_probe_yaml(probe: Dict[str, Any], indent: str) -> str:
    """生成单个 probe 的 YAML"""
    lines = []
    
    if 'httpGet' in probe:
        lines.append(f"{indent}httpGet:")
        lines.append(f"{indent}  path: {probe['httpGet']['path']}")
        lines.append(f"{indent}  port: {probe['httpGet']['port']}")
    elif 'exec' in probe:
        lines.append(f"{indent}exec:")
        lines.append(f"{indent}  command:")
        for cmd in probe['exec']['command']:
            lines.append(f"{indent}    - {cmd}")
    elif 'tcpSocket' in probe:
        lines.append(f"{indent}tcpSocket:")
        lines.append(f"{indent}  port: {probe['tcpSocket']['port']}")
    
    # 添加通用参数
    if 'initialDelaySeconds' in probe:
        lines.append(f"{indent}initialDelaySeconds: {probe['initialDelaySeconds']}")
    if 'periodSeconds' in probe:
        lines.append(f"{indent}periodSeconds: {probe['periodSeconds']}")
    if 'timeoutSeconds' in probe:
        lines.append(f"{indent}timeoutSeconds: {probe['timeoutSeconds']}")
    if 'failureThreshold' in probe:
        lines.append(f"{indent}failureThreshold: {probe['failureThreshold']}")
    if 'successThreshold' in probe:
        lines.append(f"{indent}successThreshold: {probe['successThreshold']}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Health Check YAML 生成器')
    parser.add_argument('--name', '-n', default='my-app', help='应用名称')
    parser.add_argument('--type', '-t', 
                       choices=list(PROBE_TEMPLATES.keys()),
                       required=True,
                       help='应用类型')
    parser.add_argument('--image', '-i', required=True, help='容器镜像')
    parser.add_argument('--port', '-p', type=int, default=8080, help='容器端口')
    
    args = parser.parse_args()
    
    yaml = generate_deployment_yaml(args.name, args.type, args.image, args.port)
    print(yaml)


if __name__ == "__main__":
    main()
