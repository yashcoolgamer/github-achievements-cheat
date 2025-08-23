import os

import requests
from dotenv import load_dotenv, set_key
from git import Repo

# 加载 .env 文件
load_dotenv()


# 1️⃣ 获取当前用户名的函数（通过 GitHub API）
def get_github_username():
    token = os.getenv("GITHUB_PAT")
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
        set_key('.env', 'GITHUB_USERNAME', username)
        return username
    else:
        raise Exception(f"无法获取用户名：{response.status_code} - {response.json().get('message')}")


# 2️⃣ Star 一个仓库的函数
def star_a_repo(owner, repo_name):
    token = os.getenv("GITHUB_PAT")
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


# 3️⃣ 克隆指定仓库（使用 HTTPS + PAT）
def clone_repo(owner, repo_name):
    username = get_github_username()
    token = os.getenv("GITHUB_PAT")

    clone_url = f"https://{username}:{token}@github.com/{owner}/{repo_name}.git"
    print(f"📥 正在克隆 {clone_url} ...")

    try:
        Repo.clone_from(clone_url, repo_name, config=["http.sslVerify=false"])
        print(f"✔️ 仓库克隆成功到 {repo_name} 目录")
    except Exception as e:
        raise Exception(f"克隆失败：{e}")


# 🔍 主程序入口
if __name__ == "__main__":
    REPO_OWNER = os.getenv("REPO_OWNER")
    REPO_NAME = os.getenv("REPO_NAME")

    try:
        # 获取用户名（即当前认证用户）
        username = get_github_username()
        print(f"👨‍💻 当前 GitHub 用户名：{username}")

        # Star 某个仓库
        star_a_repo(REPO_OWNER, REPO_NAME)

        # 克隆仓库
        clone_repo(REPO_OWNER, REPO_NAME)

    except Exception as e:
        print(f"发生了错误: {e}")
