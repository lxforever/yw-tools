# -*- coding: utf8 -*-
import requests
import json
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='zabbix_update_template.log',
    filemode='a'
)

def get_auth_token(url, user, password):
    """
    获取Zabbix API认证令牌
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": user,
            "password": password
        },
        "id": 1
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
        if response.status_code == 200:
            try:
                result = response.json().get('result')
                return result
            except ValueError:
                logging.error("认证响应 JSON 解析失败")
                return None
        else:
            logging.error(f"认证请求失败，HTTP 状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"认证请求异常: {e}")
        return None


def get_host_id_by_name(url, auth_token, host_name):
    """
    根据主机名获取主机ID
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid"],
            "filter": {
                "host": [host_name]
            }
        },
        "auth": auth_token,
        "id": 1
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logging.error(f"获取主机ID请求失败，HTTP 状态码: {response.status_code}")
            return None

        try:
            data = response.json()
            if not data.get('result'):
                logging.warning("未找到主机信息，请确认主机名是否正确")
                return None

            return data['result'][0].get('hostid')

        except ValueError:
            logging.error("获取主机ID响应 JSON 解析失败")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"获取主机ID请求异常: {e}")
        return None


def update_host_template(url, auth_token, host_id, template_ids):
    """
    更新主机的模板ID（支持多个模板）
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": host_id,
            "templates_clear": [],
            "templates": [
                {"templateid": tid} for tid in template_ids
            ]
        },
        "auth": auth_token,
        "id": 1
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logging.error(f"更新模板请求失败，HTTP 状态码: {response.status_code}")
            return {}

        try:
            return response.json()
        except ValueError:
            logging.error("更新模板响应 JSON 解析失败")
            return {}

    except requests.exceptions.RequestException as e:
        logging.error(f"更新模板请求异常: {e}")
        return {}


def main():
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="Zabbix 主机模板更新工具")
    parser.add_argument('--user', required=True, help='Zabbix 用户名')
    parser.add_argument('--password', required=True, help='Zabbix 密码')
    parser.add_argument('--host', required=True, help='主机名')
    parser.add_argument('--template_ids', required=True, help='模板ID列表，用逗号分隔，例如：30622,30633')
    parser.add_argument('--url', default="http://zabbix.xxx.com:9000/api_jsonrpc.php", help='Zabbix API URL')

    args = parser.parse_args()

    zabbix_user = args.user
    zabbix_password = args.password
    host_name = args.host
    zabbix_url = args.url
    new_template_ids = args.template_ids.split(',')

    # 获取认证令牌
    auth_token = get_auth_token(zabbix_url, zabbix_user, zabbix_password)
    if not auth_token:
        logging.error("无法获取认证令牌")
        exit(1)

    # 获取主机ID
    host_id = get_host_id_by_name(zabbix_url, auth_token, host_name)
    if not host_id:
        logging.error(f"未找到主机名 {host_name} 对应的主机ID")
        exit(1)

    # 更新主机的模板ID
    response = update_host_template(zabbix_url, auth_token, host_id, new_template_ids)
    if response.get('result'):
        logging.info(f"成功更新主机 {host_name} 的模板ID为 {new_template_ids}")
        exit(0)
    else:
        logging.error(f"更新主机 {host_name} 的模板ID失败: {response}")
        exit(1)


if __name__ == "__main__":
    main()
