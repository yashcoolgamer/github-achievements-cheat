import os

import requests
from dotenv import load_dotenv, set_key

# 加载 .env 文件
load_dotenv()


# 1️⃣ 获取当前用户名的函数（通过 GitHub API）
def get_github_username():
    token = os.getenv("GITHUB_PAT_1")
    if not token:
        raise ValueError("GITHUB_PAT 未在 .env 中设置")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = "https://api.github.com/user"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        username = response.json()['login']
        set_key('.env', 'GITHUB_USERNAME_1', username)
        return username
    else:
        raise Exception(f"无法获取用户名：{response.status_code} - {response.json().get('message')}")


# 2️⃣ Star 仓库
def star_a_repo(owner, repo_name):
    token = os.getenv("GITHUB_PAT_1")
    if not token:
        raise ValueError("GITHUB_PAT 未在 .env 中设置")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/user/starred/{owner}/{repo_name}"
    response = requests.put(url, headers=headers)

    if response.status_code == 204:
        print(f"✅ 已成功 star {owner}/{repo_name}")
    else:
        raise Exception(f"❌ Star 操作失败：{response.status_code} - {response.text}")


# 3️⃣ Fork 仓库
def fork_repo(owner, repo_name):
    token = os.getenv("GITHUB_PAT_1")
    if not token:
        raise ValueError("GITHUB_PAT 未在 .env 中设置")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{owner}/{repo_name}/forks"
    response = requests.post(url, headers=headers)

    if response.status_code == 202:
        print(f"✔️ 仓库 {owner}/{repo_name} fork 成功")
    else:
        raise Exception(f"❌ fork 操作失败：{response.status_code} - {response.text}")


# 🔍 主程序入口
if __name__ == "__main__":
    REPO_OWNER = os.getenv("REPO_OWNER")
    REPO_NAME = os.getenv("REPO_NAME")

    try:
        # 获取用户名（即当前认证用户）
        username = get_github_username()
        print(f"👨‍💻 当前 GitHub 用户名：{username}")

        # Star 仓库
        star_a_repo(REPO_OWNER, REPO_NAME)

        # Fork 仓库
        fork_repo(REPO_OWNER, REPO_NAME)

    except Exception as e:
        print(f"发生了错误: {e}")
